/* Generic media renderer. It consumes media records only and never persists node state. */
(function exposeWorkbenchMediaRenderer(global) {
    'use strict';

    function legacyPayload(node) {
        const legacy = node && node.extensions && node.extensions.legacy;
        return legacy && legacy.payload && typeof legacy.payload === 'object' ? legacy.payload : {};
    }

    function asItems(value) {
        return Array.isArray(value) ? value : value == null ? [] : [value];
    }

    function mediaItems(node) {
        const payload = legacyPayload(node);
        const candidates = [payload.url, payload.media, payload.images, payload.outputs, node && node.output_refs];
        const seen = new Set();
        return candidates.flatMap(asItems).map(item => {
            const source = typeof item === 'string' ? {url: item} : item || {};
            const url = String(source.url || source.src || source.preview_url || '').trim();
            if (!url || seen.has(url)) return null;
            seen.add(url);
            return {url, label: String(source.name || source.title || ''), mediaType: String(source.media_type || source.kind || source.type || '')};
        }).filter(Boolean);
    }

    function mediaKind(item) {
        const classifier = global.WorkbenchCanvasMediaKind;
        if (!classifier) throw new Error('MediaRenderer requires WorkbenchCanvasMediaKind');
        return classifier.kindForItem({
            url: item?.url || '',
            kind: item?.mediaType || '',
            name: item?.label || '',
        }, {allowWorkflow:true});
    }

    function isVideo(item) {
        return mediaKind(item) === 'video';
    }

    function preserveNativeMediaInteraction(media) {
        // Canvas cards use pointer events for selection and dragging. Native media
        // controls must not bubble those events into the card: a bubbled click can
        // trigger a re-render and recreate the video at its initial play state.
        // Do not preventDefault here; the browser still owns play/pause and seek.
        ['pointerdown', 'mousedown', 'click', 'dblclick', 'contextmenu', 'wheel'].forEach(type => {
            media.addEventListener(type, event => event.stopPropagation());
        });
    }

    function canRender(node) {
        return Boolean(node && (node.kind === 'asset' || mediaItems(node).length));
    }

    function mountInto(contentHost, node, options) {
        if (!contentHost) throw new TypeError('MediaRenderer requires a content host');
        if (!canRender(node)) throw new TypeError('MediaRenderer requires an asset node or media record');
        const documentRef = (options && options.document) || contentHost.ownerDocument || global.document;
        const root = documentRef.createElement('div');
        root.className = 'workbench-media-renderer';
        const items = mediaItems(node);
        root.classList.toggle('workbench-media-renderer--multiple', items.length > 1);
        if (!items.length) {
            root.textContent = 'No media attached';
        } else {
            items.forEach(item => {
                const media = documentRef.createElement(isVideo(item) ? 'video' : 'img');
                media.className = 'workbench-media-renderer__item';
                media.src = item.url;
                media.dataset.url = item.url;
                media.alt = item.label || node.title || 'Media';
                media.loading = 'lazy';
                if (media.tagName === 'VIDEO') {
                    media.controls = true;
                    media.preload = 'metadata';
                    media.playsInline = true;
                    preserveNativeMediaInteraction(media);
                }
                root.append(media);
            });
        }
        contentHost.replaceChildren(root);
        return Object.freeze({element: root, destroy: () => root.remove()});
    }

    function mount(shell, node, options) {
        if (!shell || !shell.contentHost) throw new TypeError('MediaRenderer requires a NodeShell content host');
        return mountInto(shell.contentHost, node, options);
    }

    function mediaSummary(items) {
        const counts = new Map();
        items.forEach(item => {
            const kind = ({image:'图片', video:'视频', audio:'音频', text:'文本', file:'文件', workflow:'工作流'})[mediaKind(item)] || '图片';
            counts.set(kind, (counts.get(kind) || 0) + 1);
        });
        return [...counts.entries()].map(([kind, count]) => `${kind} ${count}`).join(' · ');
    }

    if(global.WorkbenchNodeInspector){
        global.WorkbenchNodeInspector.registerSectionProvider({id: 'legacy', version: '1'}, 'media-renderer', node => {
            const items = mediaItems(node);
            if(!items.length) return null;
            return {
                id: 'media-renderer',
                title: '媒体',
                fields: [
                    {id: 'media-count', label: '数量', value: `${items.length} 项`},
                    {id: 'media-summary', label: '类型', value: mediaSummary(items)},
                ],
            };
        });
    }

    global.WorkbenchMediaRenderer = Object.freeze({canRender, mediaItems, mount, mountInto});
}(window));
