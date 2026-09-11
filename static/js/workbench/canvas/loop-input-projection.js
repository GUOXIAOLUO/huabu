/* Neutral batching rules for loop image/video inputs. */
(function exposeLoopInputProjection(global) {
    'use strict';
    function batch(refs, start, batchSize, index) {
        const items = Array.isArray(refs) ? refs.filter(ref => ref?.url) : [];
        if (!items.length) return [];
        const base = Math.max(1, Number(start) || 1);
        const size = Math.max(1, Math.min(100, Number(batchSize) || 1));
        const current = Math.max(1, Number(index) || base);
        return items.slice(Math.max(0, current - 1), Math.max(0, current - 1) + size);
    }
    function select(items, start, index) {
        const values = Array.isArray(items) ? items.filter(value => String(value || '').trim()) : [];
        if (!values.length) return '';
        const base = Math.max(1, Number(start) || 1);
        const current = Math.max(1, Number(index) || base);
        return values[(current - 1) % values.length] || '';
    }
    const TYPED_INPUT_SOURCE_TYPES = new Set(['asset_version', 'artifact_version', 'entity_ref', 'entity_version', 'collection', 'literal']);
    function inputBindingSourceIds(bindings, nodes) {
        if (!Array.isArray(bindings)) return null;
        const typed = bindings.filter(binding => binding && binding.enabled !== false
            && TYPED_INPUT_SOURCE_TYPES.has(binding.source_type)
            && String(binding.source_ref || '').trim())
            .sort((left, right) => (Number(left.order) || 0) - (Number(right.order) || 0)
                || String(left.id || '').localeCompare(String(right.id || '')));
        if (!typed.length) return null;
        const list = Array.isArray(nodes) ? nodes : [];
        if (!list.length) return typed.map(binding => binding.source_ref);
        return typed.map(binding => list.find(candidate => candidate?.id === binding.source_ref
            || (Array.isArray(candidate?.output_refs) && candidate.output_refs.some(reference => reference?.id === binding.source_ref))))
            .filter(Boolean).map(candidate => candidate.id);
    }
    function sourceNodes(node, connections, nodes, bindings, allowLegacyEdgeFallback = false) {
        const boundIds = inputBindingSourceIds(bindings, nodes);
        if (boundIds !== null) {
            const byId = new Map((Array.isArray(nodes) ? nodes : []).map(candidate => [candidate?.id, candidate]));
            return boundIds.map(id => byId.get(id)).filter(Boolean);
        }
        if (!allowLegacyEdgeFallback) return [];
        const list = Array.isArray(nodes) ? nodes : [];
        const byId = new Map(list.map(candidate => [candidate?.id, candidate]));
        return (Array.isArray(connections) ? connections : []).filter(connection => connection?.to === node?.id)
            .map(connection => byId.get(connection.from)).filter(Boolean);
    }
    function promptItems(node, connections = [], nodes = [], renderLoop, bindings = node?.input_bindings, allowLegacyEdgeFallback = false) {
        if (!node?.showPrompt) return [];
        const visited = new Set([node.id]);
        const findNode = id => (Array.isArray(nodes) ? nodes : []).find(candidate => candidate?.id === id);
        const items = [];
        sourceNodes(node, connections, nodes, bindings, allowLegacyEdgeFallback).forEach(source => {
                if (visited.has(source.id)) return;
                visited.add(source.id);
                if (source.type === 'prompt') {
                    const text = String(source.text || '').trim();
                    if (text) items.push(text);
                    return;
                }
                if (source.type === 'promptGroup') {
                    (source.items || []).map(findNode).filter(Boolean).forEach(prompt => {
                        const text = String(prompt.text || '').trim();
                        if (text) items.push(text);
                    });
                    return;
                }
                const text = source.type === 'loop' && typeof renderLoop === 'function'
                    ? renderLoop(source)
                    : source.type === 'llm' ? source.outputText || '' : '';
                if (String(text || '').trim()) items.push(String(text).trim());
            });
        return items;
    }
    function legacyPromptItems(node, connections = [], nodes = [], renderLoop, bindings = node?.input_bindings) {
        return promptItems(node, connections, nodes, renderLoop, bindings, true);
    }
    function connectedBatch(node, connections = [], resolve, start, batchSize, index, enabled = true, bindings = node?.input_bindings, allowLegacyEdgeFallback = false) {
        if (!enabled || !node?.id || typeof resolve !== 'function') return [];
        const sourceIds = inputBindingSourceIds(bindings, undefined);
        const refs = (sourceIds === null && allowLegacyEdgeFallback ? connections.filter(connection => connection?.to === node.id).map(connection => connection.from) : (sourceIds || []))
            .flatMap(sourceId => resolve(sourceId))
            .filter(ref => ref?.url);
        return batch(refs, start, batchSize, index);
    }
    function legacyConnectedBatch(node, connections = [], resolve, start, batchSize, index, enabled = true, bindings = node?.input_bindings) {
        return connectedBatch(node, connections, resolve, start, batchSize, index, enabled, bindings, true);
    }
    function outputMediaRefs(items = [], kind, outputValue, kindOfOutput, nameForUrl, nodeId, extension = 'png', useOriginalIndex = true) {
        const value = typeof outputValue === 'function' ? outputValue : (item => item?.url || '');
        const classify = typeof kindOfOutput === 'function' ? kindOfOutput : (item => item?.kind || 'image');
        const matches = (Array.isArray(items) ? items : []).map((item, index) => ({item, index}))
            .filter(entry => classify(entry.item) === kind)
        return matches.map(({item, index}, matchIndex) => {
                const url = value(item);
                if (!url) return null;
                const name = typeof nameForUrl === 'function' ? nameForUrl(url) : '';
                const outputIndex = useOriginalIndex ? index : matchIndex;
                return {url, name:name || `output-${outputIndex + 1}.${extension}`, kind, ...(nodeId ? {nodeId, outputIndex} : {})};
            }).filter(Boolean);
    }
    function nodeMediaRefs(node, kind, options = {}) {
        if (!node) return [];
        const nodes = Array.isArray(options.nodes) ? options.nodes : [];
        const mediaKind = typeof options.mediaKindForNode === 'function' ? options.mediaKindForNode : (() => kind);
        const makeRef = item => ({url:item.url, name:item.name || kind, role:item.role || '', kind});
        if (node.type === 'image' && node.url && mediaKind(node) === kind) return [makeRef(node)];
        if (node.type === 'group') return (node.items || []).map(id => nodes.find(candidate => candidate?.id === id))
            .filter(item => item?.type === 'image' && item?.url && mediaKind(item) === kind).map(makeRef);
        if (node.type === 'output') {
            const refs = outputMediaRefs(node.images, kind, options.outputValue, options.kindOfOutput, options.nameForUrl, kind === 'video' ? node.id : '', kind === 'video' ? 'mp4' : 'png', kind === 'video');
            return typeof options.excludeUrl === 'function' ? refs.filter(ref => !options.excludeUrl(ref.url)) : refs;
        }
        if (Array.isArray(options.generatedTypes) && options.generatedTypes.includes(node.type) && typeof options.generatedRefs === 'function') {
            return options.generatedRefs(node).filter(ref => ref?.kind === kind);
        }
        return [];
    }
    function config(node = {}, countValue) {
        const count = typeof countValue === 'function' ? countValue(node.count) : Math.max(1, Math.min(100, Number(node.count || 1) || 1));
        return Object.freeze({count, loopStart:Math.max(1, Number(node.loopStart) || 1), imageBatchSize:Math.max(1, Math.min(100, Number(node.imageBatchSize) || 1)), mode:node.mode === 'parallel' ? 'parallel' : 'serial', showPrompt:Boolean(node.showPrompt), imageInput:Boolean(node.imageInput), videoInput:false});
    }
    function summary(imageInputCount = 0, promptItemCount = 0) {
        const images = Math.max(0, Number(imageInputCount) || 0);
        const prompts = Math.max(0, Number(promptItemCount) || 0);
        return Object.freeze({imageInputCount:images, promptItemCount:prompts, hasUpstreamPrompt:prompts > 0});
    }
    global.WorkbenchCanvasLoopInputProjection = Object.freeze({batch, select, promptItems, legacyPromptItems, connectedBatch, legacyConnectedBatch, outputMediaRefs, nodeMediaRefs, config, summary});
}(window));
