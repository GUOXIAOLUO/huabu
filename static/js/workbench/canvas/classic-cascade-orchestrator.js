/*
 * static/js/workbench/canvas/classic-cascade-orchestrator.js
 *
 * Wave 14 of R4-38 — bounded compat seam for the Classic "one-click
 * run" cascade orchestrator. Moves the entire cascade state machine
 * + multi-node orchestration logic behind a shared seam so canvas.js
 * no longer owns Canvas product runtime responsibilities.
 *
 * State (page-mutable closures now owned by the seam):
 *   - loopContext         (let, nullable)
 *   - cascadeRunningIds   (Set<string>)
 *   - cascadeStopIds      (Set<string>)
 *   - cascadeSerialIds    (Set<string>)
 *   - cascadeContexts     (Map<string, ctx>)
 *
 * Helpers + main runner (moved into the seam factory):
 *   - cascadeContextFor / isCascadeActive / isCascadeStopping
 *   - cascadeAbortError / isCascadeAbortError
 *   - cascadeStopMessage / cascadeBackendRestartMessage
 *   - normalizeCanvasTaskError
 *   - clearCascadeNodeState / createCascadeContext
 *   - clearCascadeCleanupTimer / beginCascade / queueCascadeCleanup
 *   - requestCascadeStop / ensureCascadeActive / finalizeCascade
 *   - cascadeTargetIdFromOptions / cascadeContextFromOptions
 *   - cascadeFetch
 *   - computeCascadeOrder / upstreamNodeIds / resolveCascadeLoop
 *   - cascadeUiNodeIds
 *   - cascadeParallelLimit / runLimitedCascadeRounds
 *   - canvasRunTypes / canvasWorkflowEdges
 *   - computeConnectedWorkflowOrder
 *   - runCascadeNodeByType / runCascadeNodeWithLoopContext
 *   - runCanvasGenerateLegacy / runCanvasGenerate
 *   - runOneCascadePass
 *   - bindCascadeButtons / runNodeCascade
 *   - retryNodeAndDownstream / cancelCascade
 *
 * Page-side wrappers (kept as thin 1-liners in canvas.js):
 *   - cancelCascade, retryNodeAndDownstream, runNodeCascade,
 *     ensureCascadeActive, isCascadeActive, isCascadeStopping,
 *     requestCascadeStop, cascadeTargetIdFromOptions,
 *     cascadeContextFor, cascadeContextFromOptions, cascadeFetch,
 *     isCascadeAbortError, cascadeAbortError, cascadeStopMessage,
 *     cascadeBackendRestartMessage, normalizeCanvasTaskError,
 *     clearCascadeNodeState, cascadeUiNodeIds,
 *     runCascadeNodeWithLoopContext, runCanvasGenerateLegacy,
 *     runCanvasGenerate, runCascadeNodeByType, computeCascadeOrder,
 *     upstreamNodeIds, resolveCascadeLoop, bindCascadeButtons,
 *     resetCascadeRuntimeState
 *
 * R8 owns the real executor-driven cascade orchestration. R4-38
 * Wave 14 establishes the bounded compat boundary: the cascade
 * state machine stays page-side helpers but is reachable only
 * through this seam.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM + i18n + utilities
        'tr', 'langIsEn', 'nowMs', 'uid',
        'escapeHtml', 'escapeAttr',
        'loopCount',
        // Graph source-of-truth (closure getters)
        'getNodes', 'getConnections',
        // Graph effect (mutates node state and re-renders)
        'refreshNodes',
        // Execution-state seam; cascade cleanup must not write node status directly.
        'setNodeRunStatus',
        // Legacy executor primitives (type-dispatched from cascade orchestrator)
        'runGenerator', 'runMidjourneyNode', 'runMsGenNode',
        'runComfyNode', 'runLTXDirectorNode', 'runLLMNode',
        'runVideoNode', 'runRhNode', 'runMiniMaxNode',
        // UI affordances
        'setStatus', 'showErrorModal',
        'alert',
        // Shared topology helpers (Wave 14 splits canvasWorkflowEdges out)
        'computeCascadeOrderTarget',
        // comfyBackendCount is used for cascadeParallelLimit
        'comfyBackendCount',
        // Bridge: when the seam mutates its internal loopContext the
        // page-side `let loopContext` mirror must stay in sync (used by
        // renderLoopPrompt / loopInputPrompt / loopInputImageRefs /
        // loopInputVideoRefs default-arg fallback).
        'setLoopContextMirror'
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicCascadeOrchestrator.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicCascadeOrchestrator.create: missing required host op "' + name + '"');
            }
        }

        var tr = host.tr;
        var langIsEn = host.langIsEn;
        var nowMs = host.nowMs;
        var uid = host.uid;
        var escapeHtml = host.escapeHtml;
        var escapeAttr = host.escapeAttr;
        var loopCount = host.loopCount;
        var getNodes = host.getNodes;
                        var getConnections = host.getConnections;
        var refreshNodes = host.refreshNodes;
        var setNodeRunStatus = host.setNodeRunStatus;
        var runGenerator = host.runGenerator;
        var runMidjourneyNode = host.runMidjourneyNode;
        var runMsGenNode = host.runMsGenNode;
        var runComfyNode = host.runComfyNode;
        var runLTXDirectorNode = host.runLTXDirectorNode;
        var runLLMNode = host.runLLMNode;
        var runVideoNode = host.runVideoNode;
        var runRhNode = host.runRhNode;
        var runMiniMaxNode = host.runMiniMaxNode;
        var setStatus = host.setStatus;
        var showErrorModal = host.showErrorModal;
        var alert = host.alert;
        var computeCascadeOrderTarget = host.computeCascadeOrderTarget;
        var comfyBackendCount = host.comfyBackendCount;
        var setLoopContextMirror = host.setLoopContextMirror;

        // ── Cascade state (closure-mutable; replaces page-side globals) ──
        var loopContext = null;
        function setLoopContext(value){
            loopContext = value || null;
            if(typeof setLoopContextMirror === 'function'){
                try { setLoopContextMirror(loopContext); } catch(_) {}
            }
        }
        var cascadeRunningIds = new Set();
        var cascadeStopIds = new Set();
        var cascadeSerialIds = new Set(); // 记录以串行循环模式启动的运行，用于停止按钮
        var cascadeContexts = new Map();

        function resetCascadeRuntimeState() {
            cascadeRunningIds.clear();
            cascadeStopIds.clear();
            cascadeSerialIds.clear();
            cascadeContexts.forEach(function (ctx) { clearCascadeCleanupTimer(ctx); });
            cascadeContexts.clear();
            setLoopContext(null);
        }

        // ── Context lookup / predicates ──
        function cascadeContextFor(targetId) {
            return targetId ? cascadeContexts.get(targetId) || null : null;
        }
        function isCascadeActive(targetId) {
            var ctx = cascadeContextFor(targetId);
            return Boolean(ctx && (ctx.status === 'running' || ctx.status === 'stopping'));
        }
        function isCascadeStopping(targetId) {
            return cascadeContextFor(targetId) && cascadeContextFor(targetId).status === 'stopping';
        }

        // ── Error / messaging ──
        function cascadeAbortError(arg) {
            var message = (arg && typeof arg.message === 'string') ? arg.message : '已停止一键运行';
            var err = new Error(message);
            err.name = 'CascadeAbortError';
            err.isCascadeAbort = true;
            return err;
        }
        function isCascadeAbortError(err) {
            return Boolean(err && (err.isCascadeAbort || err.name === 'CascadeAbortError'));
        }
        function cascadeStopMessage(arg) {
            var reason = (arg && typeof arg.reason === 'string') ? arg.reason : '';
            if (reason) return reason;
            return langIsEn() ? 'One-click run stopped' : '已停止一键运行';
        }
        function cascadeBackendRestartMessage() {
            return langIsEn() ? 'Backend restarted and task status was lost. This one-click run has been stopped.' : '后端已重启，任务状态已丢失，本次一键运行已停止';
        }
        function normalizeCanvasTaskError(arg) {
            var err = arg && arg.err;
            var fallback = (arg && typeof arg.fallback === 'string') ? arg.fallback : '';
            var raw = (err && err.message) || String(err || '');
            var text = String(raw || '').trim();
            if (!text) return fallback || tr('canvas.generationFailed');
            if (/backend restarted and task status was lost/i.test(text)) return cascadeBackendRestartMessage();
            if (/(404|not found|missing)/i.test(text) && /canvas-image-task/i.test(text)) return cascadeBackendRestartMessage();
            if (/Failed to fetch|NetworkError|Load failed|ERR_CONNECTION_REFUSED|ERR_CONNECTION_RESET/i.test(text)) return cascadeBackendRestartMessage();
            return text;
        }

        // ── Per-node state cleanup ──
        function clearCascadeNodeState(arg) {
            var node = arg && arg.node;
            var options = (arg && arg.options) || {};
            if (!node) return;
            var keepError = Boolean(options.keepError);
            if (node.runStatus || node.runError) setNodeRunStatus(node, '', '');
            if (node._cascadeIdx) node._cascadeIdx = '';
            if (!keepError) {
                if (node.runStatus || node.runError) setNodeRunStatus(node, '', '');
                node._cascadeFailed = false;
            }
        }

        // ── Context lifecycle ──
        function createCascadeContext(arg) {
            var targetId = arg.targetId;
            var order = arg.order || [];
            var options = arg.options || {};
            var ctx = {
                targetId: targetId,
                order: [].concat(order || []),
                status: 'running',
                startedAt: nowMs(),
                abortRequested: false,
                message: '',
                currentNodeId: '',
                currentRoundLabel: '',
                mode: options.mode || 'serial',
                cleanupTimer: null,
                controllers: new Set()
            };
            cascadeContexts.set(targetId, ctx);
            return ctx;
        }
        function clearCascadeCleanupTimer(ctx) {
            if (!ctx || !ctx.cleanupTimer) return;
            clearTimeout(ctx.cleanupTimer);
            ctx.cleanupTimer = null;
        }
        function beginCascade(arg) {
            var targetId = arg.targetId;
            var order = arg.order || [];
            var options = arg.options || {};
            var existing = cascadeContextFor(targetId);
            if (existing) {
                clearCascadeCleanupTimer(existing);
                cascadeContexts.delete(targetId);
            }
            var ctx = createCascadeContext({ targetId: targetId, order: order, options: options });
            cascadeRunningIds.add(targetId);
            if (options.serial) cascadeSerialIds.add(targetId);
            if (options.mode) ctx.mode = options.mode;
            return ctx;
        }
        function queueCascadeCleanup(arg) {
            var ctx = arg && arg.ctx;
            var ids = (arg && arg.ids) || [];
            if (!ctx) return;
            clearCascadeCleanupTimer(ctx);
            ctx.cleanupTimer = setTimeout(function () {
                var nodes = getNodes();
                var connections = getConnections();
                var uniqueIds = [].concat(ids || []).filter(function (v, i, arr) {
                    return Boolean(v) && arr.indexOf(v) === i;
                });
                uniqueIds.forEach(function (id) {
                    var node = nodes.find(function (n) { return n.id === id; });
                    if (node && node.runStatus === 'done') clearCascadeNodeState({ node: node, options: { keepError: false } });
                });
                refreshNodes(uniqueIds);
                if (cascadeContexts.get(ctx.targetId) === ctx) cascadeContexts.delete(ctx.targetId);
                ctx.cleanupTimer = null;
            }, 3000);
        }
        function requestCascadeStop(arg) {
            var targetId = arg && arg.targetId;
            var reason = (arg && arg.reason) || '';
            if (!targetId) return;
            cascadeStopIds.add(targetId);
            var ctx = cascadeContextFor(targetId);
            if (ctx) {
                ctx.abortRequested = true;
                ctx.status = 'stopping';
                if (reason) ctx.message = reason;
                var controllers = Array.from(ctx.controllers || []);
                controllers.forEach(function (controller) {
                    try { controller.abort(); } catch (_) {}
                });
            }
            refreshNodes(cascadeUiNodeIds({ targetId: targetId, order: null }));
        }
        function ensureCascadeActive(arg) {
            var targetId = arg && arg.targetId;
            var reason = (arg && arg.reason) || '';
            var ctx = cascadeContextFor(targetId);
            if (!ctx) return null;
            if (ctx.abortRequested || ctx.status === 'stopping') throw cascadeAbortError({ message: cascadeStopMessage({ reason: reason || ctx.message }) });
            return ctx;
        }
        function finalizeCascade(arg) {
            var targetId = arg && arg.targetId;
            var state = arg && arg.state;
            var options = (arg && arg.options) || {};
            var ctx = cascadeContextFor(targetId);
            var order = options.order || (ctx && ctx.order) || null;
            if (order == null) {
                order = computeCascadeOrderTarget ? computeCascadeOrderTarget({ targetId: targetId }) : [];
            }
            var uiIds = cascadeUiNodeIds({ targetId: targetId, order: order });
            clearCascadeCleanupTimer(ctx);
            cascadeRunningIds.delete(targetId);
            cascadeStopIds.delete(targetId);
            cascadeSerialIds.delete(targetId);
            if (ctx) ctx.status = state;
            if (state === 'done') {
                queueCascadeCleanup({ ctx: ctx, ids: uiIds });
                refreshNodes(uiIds);
                return;
            }
            if (state === 'stopped') {
                (order || []).forEach(function (id) {
                    var nodes = getNodes();
                    var node = nodes.find(function (n) { return n.id === id; });
                    if (node && !node._cascadeFailed) clearCascadeNodeState({ node: node });
                });
            }
            refreshNodes(uiIds);
            cascadeContexts.delete(targetId);
        }
        function cascadeTargetIdFromOptions(arg) {
            var options = (arg && arg.options) || {};
            return String(options.cascadeTargetId || options.targetId || '');
        }
        function cascadeContextFromOptions(arg) {
            return cascadeContextFor(cascadeTargetIdFromOptions({ options: (arg && arg.options) || {} }));
        }
        function cascadeFetch(arg) {
            var input = arg && arg.input;
            var init = (arg && arg.init) || {};
            var options = (arg && arg.options) || {};
            var ctx = cascadeContextFromOptions({ options: options });
            if (!ctx) return fetch(input, init);
            ensureCascadeActive({ targetId: ctx.targetId, reason: ctx.message });
            var controller = new AbortController();
            ctx.controllers.add(controller);
            try {
                return fetch(input, Object.assign({}, init, { signal: controller.signal }));
            } catch (err) {
                if (controller.signal.aborted || (err && err.name === 'AbortError')) {
                    throw cascadeAbortError({ message: cascadeStopMessage({ reason: ctx.message }) });
                }
                throw err;
            } finally {
                ctx.controllers.delete(controller);
            }
        }

        // ── Topology (topological order, upstream walk, loop resolution) ──
        function canvasRunTypes() {
            return ['generator', 'midjourney', 'msgen', 'comfy', 'ltxDirector', 'llm', 'video', 'rh', 'minimax'];
        }
        function canvasWorkflowEdges() {
            var runTypes = canvasRunTypes();
            var direct = [];
            var connections = getConnections();
            var nodes = getNodes();
            connections.forEach(function (c) {
                var from = nodes.find(function (n) { return n.id === c.from; });
                var to = nodes.find(function (n) { return n.id === c.to; });
                if (!from || !to || !runTypes.includes(from.type)) return;
                if (runTypes.includes(to.type)) {
                    direct.push([from.id, to.id]);
                    return;
                }
                if (to.type === 'output') {
                    connections.filter(function (cc) { return cc.from === to.id; }).forEach(function (cc) {
                        var next = nodes.find(function (n) { return n.id === cc.to; });
                        if (next && runTypes.includes(next.type)) direct.push([from.id, next.id]);
                    });
                }
            });
            return direct;
        }
        function computeConnectedWorkflowOrder(arg) {
            var anchorId = arg && arg.anchorId;
            var nodes = getNodes();
            var runTypes = canvasRunTypes();
            var anchor = nodes.find(function (n) { return n.id === anchorId; });
            if (!anchor || !runTypes.includes(anchor.type)) return [];
            var edges = canvasWorkflowEdges();
            var connected = new Set([anchorId]);
            var changed = true;
            while (changed) {
                changed = false;
                edges.forEach(function (pair) {
                    var from = pair[0], to = pair[1];
                    if (connected.has(from) && !connected.has(to)) { connected.add(to); changed = true; }
                    if (connected.has(to) && !connected.has(from)) { connected.add(from); changed = true; }
                });
            }
            var order = [];
            var seen = new Set();
            var visit = function (id) {
                if (seen.has(id)) return;
                seen.add(id);
                edges.filter(function (pair) { return pair[1] === id; }).forEach(function (pair) {
                    var from = pair[0];
                    if (connected.has(from)) visit(from);
                });
                if (connected.has(id)) order.push(id);
            };
            nodes.filter(function (n) { return connected.has(n.id) && runTypes.includes(n.type); }).forEach(function (n) { visit(n.id); });
            return order;
        }
        function computeCascadeOrder(arg) {
            var targetId = arg && arg.targetId;
            var visited = new Set();
            var order = [];
            var GEN_TYPES = canvasRunTypes();
            var nodes = getNodes();
            var connections = getConnections();
            function dfs(id) {
                if (visited.has(id)) return;
                visited.add(id);
                var node = nodes.find(function (n) { return n.id === id; });
                if (!node) return;
                connections.filter(function (c) { return c.to === id; }).forEach(function (c) {
                    var from = nodes.find(function (n) { return n.id === c.from; });
                    if (!from) return;
                    if (GEN_TYPES.includes(from.type)) {
                        dfs(from.id);
                    } else if (from.type === 'output') {
                        connections.filter(function (cc) { return cc.to === from.id; }).forEach(function (cc) {
                            var ff = nodes.find(function (n) { return n.id === cc.from; });
                            if (ff && GEN_TYPES.includes(ff.type)) dfs(ff.id);
                        });
                    }
                });
                if (GEN_TYPES.includes(node.type)) order.push(id);
            }
            dfs(targetId);
            return order;
        }
        function upstreamNodeIds(arg) {
            var targetId = arg && arg.targetId;
            var found = new Set();
            var connections = getConnections();
            var walk = function (id) {
                connections.filter(function (c) { return c.to === id; }).forEach(function (c) {
                    if (found.has(c.from)) return;
                    found.add(c.from);
                    walk(c.from);
                });
            };
            walk(targetId);
            return found;
        }
        function resolveCascadeLoop(arg) {
            var targetId = arg && arg.targetId;
            var upstream = upstreamNodeIds({ targetId: targetId });
            var nodes = getNodes();
            var loops = nodes.filter(function (n) { return n.type === 'loop' && upstream.has(n.id); });
            if (!loops.length) return null;
            var loop = loops[loops.length - 1];
            return { node: loop, count: loopCount(loop), mode: loop.mode === 'parallel' ? 'parallel' : 'serial' };
        }
        function cascadeUiNodeIds(arg) {
            var targetId = arg && arg.targetId;
            var order = arg && typeof arg.order !== 'undefined' ? arg.order : null;
            if (order == null) order = computeCascadeOrder({ targetId: targetId });
            var ids = new Set([targetId].concat(order || []));
            var loop = resolveCascadeLoop({ targetId: targetId });
            if (loop && loop.node && loop.node.id) ids.add(loop.node.id);
            return Array.from(ids).filter(Boolean);
        }
        function cascadeParallelLimit(arg) {
            var order = (arg && arg.order) || [];
            var totalRounds = (arg && arg.totalRounds) || 1;
            var nodes = getNodes();
            var hasComfy = order.some(function (id) { return ['comfy', 'minimax'].includes(nodes.find(function (n) { return n.id === id; }) && nodes.find(function (n) { return n.id === id; }).type); });
            if (hasComfy) return Math.max(1, Math.min(totalRounds, comfyBackendCount || 1));
            return Math.max(1, Math.min(totalRounds, 6));
        }
        function runLimitedCascadeRounds(arg) {
            var rounds = (arg && arg.rounds) || [];
            var limit = arg && arg.limit;
            var runner = arg && arg.runner;
            var next = 0;
            var workers = Array.from({ length: Math.max(1, Math.min(limit, rounds.length)) }, function () {
                return (async function () {
                    while (next < rounds.length) {
                        var round = rounds[next++];
                        await runner(round);
                    }
                })();
            });
            return Promise.allSettled(workers);
        }

        // ── Type-dispatched node execution within cascade ──
        function runCascadeNodeByType(arg) {
            var node = arg && arg.node;
            var options = (arg && arg.options) || {};
            if (!node) return Promise.resolve();
            var runOpts = Object.assign({ cascade: true }, options);
            if (node.type === 'generator') return runGenerator(node.id, runOpts);
            if (node.type === 'midjourney') return runMidjourneyNode(node.id, runOpts);
            if (node.type === 'msgen') return runMsGenNode(node.id, runOpts);
            if (node.type === 'comfy') return runComfyNode(node.id, runOpts);
            if (node.type === 'ltxDirector') return runLTXDirectorNode(node.id, runOpts);
            if (node.type === 'llm') return runLLMNode(node.id, runOpts);
            if (node.type === 'video') return runVideoNode(node.id, runOpts);
            if (node.type === 'rh') return runRhNode(node.id, runOpts);
            if (node.type === 'minimax') return runMiniMaxNode(node.id, runOpts);
            return Promise.resolve();
        }
        function runCascadeNodeWithLoopContext(arg) {
            var node = arg && arg.node;
            var ctx = arg && arg.ctx;
            var opts = (arg && arg.opts) || {};
            var previous = loopContext;
            var previousNodeCtx = node ? node._activeLoopCtx : null;
            loopContext = ctx || null;
            if (node) node._activeLoopCtx = ctx || null;
            return Promise.resolve(runCascadeNodeByType({ node: node, options: opts })).finally(function () {
                loopContext = previous;
                if (node) {
                    if (previousNodeCtx) node._activeLoopCtx = previousNodeCtx;
                    else delete node._activeLoopCtx;
                }
            });
        }
        function runCanvasGenerateLegacy(arg) {
            var nodeId = arg && arg.nodeId;
            var nodes = getNodes();
            var node = nodes.find(function (n) { return n.id === nodeId; });
            if (!node || node.running || cascadeRunningIds.has(nodeId)) return Promise.resolve();
            return runCascadeNodeByType({ node: node, options: { cascade: false } });
        }
        function runCanvasGenerate(arg) {
            var nodeId = arg && arg.nodeId;
            var nodes = getNodes();
            var node = nodes.find(function (n) { return n.id === nodeId; });
            if (!node || node.running || cascadeRunningIds.has(nodeId)) return Promise.resolve();
            var compat = (typeof window !== 'undefined') && window.WorkbenchCanvasExecutionCompatibility;
            if (compat && typeof compat.run === 'function') {
                return compat.run({
                    canvasKind: 'classic',
                    sourceNodeId: nodeId,
                    execute: function () { return runCanvasGenerateLegacy({ nodeId: nodeId }); }
                }) || runCanvasGenerateLegacy({ nodeId: nodeId });
            }
            return runCanvasGenerateLegacy({ nodeId: nodeId });
        }
        function runOneCascadePass(arg) {
            var order = (arg && arg.order) || [];
            var options = (arg && arg.options) || {};
            var targetId = cascadeTargetIdFromOptions({ options: options });
            var nodes = getNodes();
            order.forEach(function (id) {
                var n = nodes.find(function (x) { return x.id === id; });
                if (n) { setNodeRunStatus(n, 'queued', ''); n._cascadeFailed = false; n._cascadeIdx = ''; }
            });
            refreshNodes(order);
            var series = Promise.resolve();
            for (var i = 0; i < order.length; i++) {
                (function (idx) {
                    series = series.then(function () {
                        if (targetId) ensureCascadeActive({ targetId: targetId });
                        var id = order[idx];
                        var nodesNow = getNodes();
                        var node = nodesNow.find(function (n) { return n.id === id; });
                        if (!node) return;
                        var ctx = cascadeContextFor(targetId);
                        if (ctx) ctx.currentNodeId = id;
                        setNodeRunStatus(node, 'running', '');
                        refreshNodes([id]);
                        return runCascadeNodeByType({ node: node, options: { cascade: true, cascadeTargetId: targetId } }).then(function () {
                            if (targetId) ensureCascadeActive({ targetId: targetId });
                            setNodeRunStatus(node, 'done', '');
                            refreshNodes([id]);
                        }).catch(function (err) {
                            setNodeRunStatus(node, 'failed', err.message || String(err));
                            node._cascadeFailed = true;
                            throw err;
                        });
                    });
                })(i);
            }
            return series;
        }

        // ── Click-binding for legacy button HTML ──
        function bindCascadeButtons(arg) {
            var wrap = arg && arg.wrap;
            var nodeId = arg && arg.nodeId;
            if (!wrap) return;
            var nodes = wrap.querySelectorAll ? wrap.querySelectorAll('[data-cascade="' + nodeId + '"]') : [];
            Array.from(nodes).forEach(function (b) {
                b.onmousedown = function (e) { e.stopPropagation(); };
                b.onclick = function (e) { e.stopPropagation(); runNodeCascade({ nodeId: nodeId }); };
            });
            var stops = wrap.querySelectorAll ? wrap.querySelectorAll('[data-cascade-stop="' + nodeId + '"]') : [];
            Array.from(stops).forEach(function (b) {
                b.onmousedown = function (e) { e.stopPropagation(); };
                b.onclick = function (e) { e.stopPropagation(); requestCascadeStop({ targetId: nodeId }); };
            });
            var retries = wrap.querySelectorAll ? wrap.querySelectorAll('[data-retry="' + nodeId + '"]') : [];
            Array.from(retries).forEach(function (b) {
                b.onmousedown = function (e) { e.stopPropagation(); };
                b.onclick = function (e) { e.stopPropagation(); retryNodeAndDownstream({ nodeId: nodeId }); };
            });
            var stops2 = wrap.querySelectorAll ? wrap.querySelectorAll('[data-stop="' + nodeId + '"]') : [];
            Array.from(stops2).forEach(function (b) {
                b.onmousedown = function (e) { e.stopPropagation(); };
                b.onclick = function (e) { e.stopPropagation(); cancelCascade({ nodeId: nodeId }); };
            });
        }

        // ── Main runner (parallel / serial / loop-aware) ──
        function runNodeCascade(arg) {
            var nodeId = arg && arg.nodeId;
            var nodes = getNodes();
            var target = nodes.find(function (n) { return n.id === nodeId; });
            if (!target) return Promise.resolve();
            if (target.running) { alert('当前节点正在运行'); return Promise.resolve(); }
            var order = computeCascadeOrder({ targetId: nodeId });
            if (!order.length) { alert('没有可运行的生成节点'); return Promise.resolve(); }
            var loop = resolveCascadeLoop({ targetId: nodeId });
            var totalRounds = (loop && loop.count) || 1;
            var startIdx = Math.max(1, Number(loop && loop.node && loop.node.loopStart) || 1);
            var loopImageStride = (loop && loop.node && loop.node.imageInput) ? Math.max(1, Math.min(100, Number(loop.node.imageBatchSize) || 1)) : 0;
            var loopBatchSize = Math.max(1, loopImageStride);
            var endIdx = startIdx + (totalRounds - 1) * loopBatchSize;
            var ctx = beginCascade({ targetId: nodeId, order: order, options: { serial: true, mode: (loop && loop.mode) || 'serial' } });

            function mapNodes() { return getNodes(); }

            refreshNodes(cascadeUiNodeIds({ targetId: nodeId, order: order }));
            order.forEach(function (id) {
                var n = mapNodes().find(function (x) { return x.id === id; });
                if (n) n.generatedOutputs = [];
            });
            if (loop && loop.mode === 'parallel' && totalRounds > 1) {
                order.forEach(function (id) {
                    var n = mapNodes().find(function (x) { return x.id === id; });
                    if (n) { setNodeRunStatus(n, 'queued', ''); n._cascadeFailed = false; n._cascadeIdx = '0/' + totalRounds; }
                });
                refreshNodes(cascadeUiNodeIds({ targetId: nodeId, order: order }));
                var done = 0;
                var rounds = Array.from({ length: totalRounds }, function (_, idx) { return { idx: idx, index: startIdx + idx * loopBatchSize }; });
                var limit = cascadeParallelLimit({ order: order, totalRounds: totalRounds });
                return runLimitedCascadeRounds({
                    rounds: rounds,
                    limit: limit,
                    runner: function (roundObj) {
                        var index = roundObj.index;
                        ensureCascadeActive({ targetId: nodeId, reason: ctx.message });
                        var loopCtx = { index: index, total: endIdx, nodeId: loop.node.id };
                        for (var i = 0; i < order.length; i++) {
                            ensureCascadeActive({ targetId: nodeId, reason: ctx.message });
                            var id = order[i];
                            var node = mapNodes().find(function (n) { return n.id === id; });
                            if (!node) continue;
                            ctx.currentNodeId = id;
                            ctx.currentRoundLabel = index + '/' + endIdx;
                            setNodeRunStatus(node, 'running', '');
                            node._cascadeIdx = (order.indexOf(id) + 1) + '/' + order.length + ' · ' + index + '/' + endIdx;
                            refreshNodes([id]);
                            runCascadeNodeWithLoopContext({ node: node, ctx: loopCtx, opts: { cascadeTargetId: nodeId } });
                            ensureCascadeActive({ targetId: nodeId, reason: ctx.message });
                            setNodeRunStatus(node, 'done', '');
                            refreshNodes([id]);
                        }
                        done += 1;
                        order.forEach(function (id) {
                            var n = mapNodes().find(function (x) { return x.id === id; });
                            if (n) n._cascadeIdx = done + '/' + totalRounds;
                        });
                        refreshNodes(order);
                    }
                }).then(function (results) {
                    loopContext = null;
                    var failed = results.find(function (r) { return r.status === 'rejected'; });
                    if (failed) {
                        var err = failed.reason || new Error('parallel loop failed');
                        if (isCascadeAbortError(err)) {
                            finalizeCascade({ targetId: nodeId, state: 'stopped', options: { order: order } });
                            return;
                        }
                        var node = mapNodes().find(function (n) { return n.id === ctx.currentNodeId; }) || mapNodes().find(function (n) { return n.id === nodeId; }) || target;
                        setNodeRunStatus(node, 'failed', err.message || String(err));
                        node._cascadeFailed = true;
                        finalizeCascade({ targetId: nodeId, state: 'failed', options: { order: order } });
                        return;
                    }
                    finalizeCascade({ targetId: nodeId, state: 'done', options: { order: order } });
                });
            }
            refreshNodes(cascadeUiNodeIds({ targetId: nodeId, order: order }));
            var serialPromise = Promise.resolve();
            for (var round = 1; round <= totalRounds; round++) {
                (function (roundNum) {
                    serialPromise = serialPromise.then(function () {
                        ensureCascadeActive({ targetId: nodeId, reason: ctx.message });
                        var loopIndex = startIdx + (roundNum - 1) * loopBatchSize;
                        setLoopContext(loop ? { index: loopIndex, total: endIdx, nodeId: loop.node.id } : null);
                        var nodesNow = mapNodes();
                        order.forEach(function (id) {
                            var n = nodesNow.find(function (x) { return x.id === id; });
                            if (n) {
                                setNodeRunStatus(n, 'queued', '');
                                n._cascadeFailed = false;
                                n._cascadeIdx = (order.indexOf(id) + 1) + '/' + order.length + (totalRounds > 1 ? ' · ' + loopIndex + '/' + endIdx : '');
                            }
                        });
                        refreshNodes(cascadeUiNodeIds({ targetId: nodeId, order: order }));
                        var inner = Promise.resolve();
                        for (var i = 0; i < order.length; i++) {
                            (function (idx) {
                                inner = inner.then(function () {
                                    var id = order[idx];
                                    var node = mapNodes().find(function (n) { return n.id === id; });
                                    if (!node) return;
                                    ctx.currentNodeId = id;
                                    ctx.currentRoundLabel = totalRounds > 1 ? loopIndex + '/' + endIdx : '';
                                    setNodeRunStatus(node, 'running', '');
                                    refreshNodes([id]);
                                    return runCascadeNodeWithLoopContext({ node: node, ctx: loopContext, opts: { cascadeTargetId: nodeId } }).then(function () {
                                        ensureCascadeActive({ targetId: nodeId, reason: ctx.message });
                                        setNodeRunStatus(node, 'done', '');
                                        refreshNodes([id]);
                                    }).catch(function (err) {
                                        loopContext = null;
                                        if (isCascadeAbortError(err)) {
                                            finalizeCascade({ targetId: nodeId, state: 'stopped', options: { order: order } });
                                            return;
                                        }
                                        setNodeRunStatus(node, 'failed', (totalRounds > 1 ? tr('canvas.loopRound') + ' ' + roundNum + '/' + totalRounds + ': ' : '') + (err.message || String(err)));
                                        node._cascadeFailed = true;
                                        for (var j = idx + 1; j < order.length; j++) {
                                            var n2 = mapNodes().find(function (x) { return x.id === order[j]; });
                                            if (n2) { setNodeRunStatus(n2, '', ''); n2._cascadeIdx = ''; }
                                        }
                                        finalizeCascade({ targetId: nodeId, state: 'failed', options: { order: order } });
                                    });
                                });
                            })(i);
                        }
                        return inner;
                    });
                })(round);
            }
            return serialPromise.then(function () {
                loopContext = null;
                finalizeCascade({ targetId: nodeId, state: 'done', options: { order: order } });
            });
        }
        function retryNodeAndDownstream(arg) {
            var nodeId = arg && arg.nodeId;
            var nodes = getNodes();
            var target = nodes.find(function (n) { return n.id === nodeId; });
            if (!target) return Promise.resolve();
            if (isCascadeActive(nodeId)) return Promise.resolve();
            var order = computeCascadeOrder({ targetId: nodeId });
            var idx = order.indexOf(nodeId);
            var remain = idx >= 0 ? order.slice(idx) : [nodeId];
            beginCascade({ targetId: nodeId, order: remain, options: { serial: true, mode: 'retry' } });
            return runOneCascadePass({ order: remain, options: { cascadeTargetId: nodeId } }).then(function () {
                finalizeCascade({ targetId: nodeId, state: 'done', options: { order: remain } });
            }).catch(function (err) {
                if (isCascadeAbortError(err)) {
                    finalizeCascade({ targetId: nodeId, state: 'stopped', options: { order: remain } });
                    return;
                }
                finalizeCascade({ targetId: nodeId, state: 'failed', options: { order: remain } });
                refreshNodes(remain);
            });
        }
        function cancelCascade(arg) {
            var nodeId = arg && arg.nodeId;
            requestCascadeStop({ targetId: nodeId });
        }

        var handle = Object.freeze({
            // state + reset
            resetCascadeRuntimeState: resetCascadeRuntimeState,
            // context lookup / predicates
            cascadeContextFor: cascadeContextFor,
            isCascadeActive: isCascadeActive,
            isCascadeStopping: isCascadeStopping,
            // error / messaging
            cascadeAbortError: cascadeAbortError,
            isCascadeAbortError: isCascadeAbortError,
            cascadeStopMessage: cascadeStopMessage,
            cascadeBackendRestartMessage: cascadeBackendRestartMessage,
            normalizeCanvasTaskError: normalizeCanvasTaskError,
            // per-node state cleanup
            clearCascadeNodeState: clearCascadeNodeState,
            // context lifecycle
            createCascadeContext: createCascadeContext,
            clearCascadeCleanupTimer: clearCascadeCleanupTimer,
            beginCascade: beginCascade,
            queueCascadeCleanup: queueCascadeCleanup,
            requestCascadeStop: requestCascadeStop,
            ensureCascadeActive: ensureCascadeActive,
            finalizeCascade: finalizeCascade,
            cascadeTargetIdFromOptions: cascadeTargetIdFromOptions,
            cascadeContextFromOptions: cascadeContextFromOptions,
            cascadeFetch: cascadeFetch,
            // topology
            canvasRunTypes: canvasRunTypes,
            canvasWorkflowEdges: canvasWorkflowEdges,
            computeConnectedWorkflowOrder: computeConnectedWorkflowOrder,
            computeCascadeOrder: computeCascadeOrder,
            upstreamNodeIds: upstreamNodeIds,
            resolveCascadeLoop: resolveCascadeLoop,
            cascadeUiNodeIds: cascadeUiNodeIds,
            cascadeParallelLimit: cascadeParallelLimit,
            runLimitedCascadeRounds: runLimitedCascadeRounds,
            // type-dispatched
            runCascadeNodeByType: runCascadeNodeByType,
            runCascadeNodeWithLoopContext: runCascadeNodeWithLoopContext,
            runCanvasGenerateLegacy: runCanvasGenerateLegacy,
            runCanvasGenerate: runCanvasGenerate,
            runOneCascadePass: runOneCascadePass,
            // click + entrypoints
            bindCascadeButtons: bindCascadeButtons,
            runNodeCascade: runNodeCascade,
            retryNodeAndDownstream: retryNodeAndDownstream,
            cancelCascade: cancelCascade
        });
        return handle;
    }

    var exposed = {
        create: create,
        REQUIRED_OPS: REQUIRED_OPS
    };
    if (typeof window !== 'undefined') {
        window.WorkbenchCanvasClassicCascadeOrchestrator = exposed;
    }
})();
