/* Neutral Canvas record-session owner.

   This module owns the mutable session cursor, dirty/save scheduling, canonical
   CAS conflict handling, remote-version polling and update-message deferral.
   The page adapter supplies only graph serialization and record projection;
   it does not participate in the persistence state machine. */
(function exposeWorkbenchCanvasSession(global) {
    'use strict';

    function requiredFunction(settings, name) {
        if (typeof settings[name] !== 'function') {
            throw new TypeError(`${name} callback is required`);
        }
        return settings[name];
    }

    function create(options) {
        const settings = options && typeof options === 'object' ? options : {};
        const serialize = requiredFunction(settings, 'serialize');
        const applyRecord = requiredFunction(settings, 'applyRecord');
        const setStatus = typeof settings.setStatus === 'function' ? settings.setStatus : () => {};
        const isVisible = typeof settings.isVisible === 'function' ? settings.isVisible : () => true;
        const persistence = global.WorkbenchCanvasPersistence;
        const schedulers = global.WorkbenchCanvasSaveScheduler;
        const remoteSyncFactory = global.WorkbenchCanvasRemoteSync;
        const updateMessages = global.WorkbenchCanvasUpdateMessage;
        if (!persistence || !schedulers || !remoteSyncFactory || !updateMessages) {
            throw new TypeError('Canvas session dependencies are required');
        }

        const clientId = String(settings.clientId || '');
        let record = null;
        let updatedAt = 0;
        let dirty = false;
        let applyingRemote = false;

        const saveScheduler = schedulers.create({
            debounceMs: Number(settings.debounceMs) || 500,
            run: saveNow,
            onRetry: () => { dirty = true; },
        });
        const remoteApply = schedulers.createRemoteApply({
            apply: () => sync(),
            defaultDelayMs: Number(settings.remoteApplyDelayMs) || 1000,
        });
        const remoteSync = remoteSyncFactory.create({
            canvasId: () => record?.id,
            currentUpdatedAt: () => updatedAt,
            currentRevision: () => persistence.revisionOf(record?.id),
            isEligible: () => Boolean(record && !applyingRemote && isVisible()),
            onNewer: () => sync(),
            intervalMs: Number(settings.remotePollIntervalMs) || 2500,
        });

        function snapshot() {
            return Object.freeze({
                canvasId: String(record?.id || ''),
                updatedAt,
                revision: Number(persistence.revisionOf(record?.id) || 0),
                dirty,
                applyingRemote,
                saving: saveScheduler.isInFlight(),
                saveScheduled: saveScheduler.hasScheduled(),
                remotePolling: remoteSync.isRunning(),
            });
        }

        async function project(nextRecord, source) {
            record = nextRecord;
            updatedAt = Number(nextRecord?.updated_at || updatedAt || Date.now());
            await applyRecord(nextRecord, Object.freeze({source}));
            return nextRecord;
        }

        async function applyRemote(nextRecord) {
            if (!nextRecord || !record || nextRecord.id !== record.id) return false;
            if (dirty || saveScheduler.hasScheduled() || saveScheduler.isInFlight() || saveScheduler.hasPendingAgain()) {
                remoteApply.schedule(1000);
                return false;
            }
            applyingRemote = true;
            try {
                dirty = false;
                await project(nextRecord, 'remote');
                setStatus('Synced');
                return true;
            } finally {
                applyingRemote = false;
            }
        }

        async function saveNow() {
            if (!record || applyingRemote) return false;
            const local = serialize();
            try {
                const result = await persistence.save(record.id, {
                    ...(local || {}),
                    client_id: clientId,
                    base_updated_at: Number(updatedAt || record.updated_at || 0),
                });
                if (result.status === 409) {
                    const remote = result.canvas;
                    if (dirty || saveScheduler.hasPendingAgain()) {
                        // Preserve the rejected local state for explicit
                        // reconciliation. Never advance the CAS cursor and
                        // auto-retry an unchanged stale payload.
                        dirty = true;
                        setStatus('Save conflict');
                        return false;
                    }
                    if (remote) await applyRemote(remote);
                    setStatus('Synced');
                    return true;
                }
                if (!result.ok) throw new Error('save failed');
                const serverRecord = result.payload?.canvas || result.canvas || {};
                const merged = {
                    ...(local || {}),
                    ...serverRecord,
                    id: record.id,
                    viewport: local?.viewport || serverRecord.viewport || record.viewport,
                };
                updatedAt = Number(result.updatedAt || merged.updated_at || Date.now());
                merged.updated_at = updatedAt;
                record = merged;
                dirty = Boolean(saveScheduler.hasPendingAgain());
                await applyRecord(merged, Object.freeze({source:'saved'}));
                setStatus('Saved');
                return true;
            } catch (error) {
                setStatus('Save failed');
                console.error(error);
                return false;
            }
        }

        async function open(canvasId) {
            setStatus('Opening...');
            remoteSync.stop();
            remoteApply.cancel();
            saveScheduler.cancel();
            const result = await persistence.load(canvasId);
            if (!result.ok || !result.canvas) throw new Error('Canvas open failed');
            dirty = false;
            applyingRemote = false;
            updatedAt = Number(result.canvas.updated_at || result.updatedAt || 0);
            await project(result.canvas, 'open');
            remoteSync.start();
            setStatus('Ready');
            return result.canvas;
        }

        function scheduleSave() {
            if (!record || applyingRemote) return false;
            dirty = true;
            setStatus('Saving...');
            saveScheduler.schedule();
            return true;
        }

        async function flush() {
            return saveScheduler.flush();
        }

        async function sync() {
            if (!record) return false;
            try {
                const meta = await persistence.metadata(record.id);
                if (!meta.ok) return false;
                const remoteRevision = Number(meta.revision || 0);
                const newer = remoteRevision > 0
                    ? remoteRevision > Number(persistence.revisionOf(record.id) || 0)
                    : Number(meta.updatedAt || 0) >= Number(updatedAt || 0);
                if (!newer) return false;
                const result = await persistence.load(record.id);
                if (!result.ok || !result.canvas) return false;
                return applyRemote(result.canvas);
            } catch (error) {
                console.error(error);
                setStatus('Sync failed');
                return false;
            }
        }

        function handleUpdate(data) {
            const update = updateMessages.newerForCanvas(data, {
                canvasId: record?.id,
                clientId,
                currentUpdatedAt: updatedAt,
                currentRevision: persistence.revisionOf(record?.id),
            });
            if (!update) return false;
            saveScheduler.cancel();
            dirty = false;
            remoteApply.schedule(saveScheduler.isInFlight() ? 700 : 120);
            setStatus('Syncing...');
            return true;
        }

        function adoptRevision(revision, missingFallback) {
            if (!record) return Number(revision) || Number(missingFallback) || 0;
            updatedAt = persistence.adoptRevision(record, revision, missingFallback);
            return updatedAt;
        }

        async function close() {
            saveScheduler.cancel();
            if (record && dirty) await saveScheduler.flush();
            remoteApply.cancel();
            remoteSync.stop();
            record = null;
            updatedAt = 0;
            dirty = false;
            applyingRemote = false;
        }

        return Object.freeze({open, scheduleSave, flush, sync, handleUpdate, adoptRevision, close, snapshot});
    }

    global.WorkbenchCanvasSession = Object.freeze({create});
}(window));
