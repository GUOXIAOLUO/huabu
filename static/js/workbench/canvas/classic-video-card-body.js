/*
 * static/js/workbench/canvas/classic-video-card-body.js
 *
 * Wave 10 of R4-38 — bounded compat seam for the Classic video-node
 * card body. One page-side function moves behind a shared seam:
 * `renderVideoBody` (~135-line body renderer that builds the
 * `video`-type generator card — provider/model selects, duration,
 * aspect, resolution, the toggle row, the media input list, and the
 * manual-URL / temp-sh action buttons). The factory half of the
 * video-node creation split into the COMPAT seam is `addVideo`
 * (already migrated by R4-38 Wave 3 to the unified
 * `classic-node-factories.js` host seam); Wave 10 closes the
 * COMPAT/COMPAT half by establishing the bounded body-render seam.
 *
 * Page-side usage (canvas.js):
 *     const videoBody = ensureClassicVideoCardBody();
 *     // body dispatcher:
 *     if(node.type === 'video') body.appendChild(videoBody.renderBody({node}));
 *
 * R8 owns the real executor-driven video-node card rendering.
 * R4-38 Wave 10 establishes the bounded compat boundary; the
 * function body stays page-side (page-owned per COMPAT/R8 semantics
 * in docs/plans/R4_CLASSIC_CAPABILITY_INVENTORY.md) but is
 * reachable only through this seam so the dispatcher and
 * seam-call shape is explicit.
 */
(function () {
    'use strict';

    var REQUIRED_OPS = [
        // DOM
        'document',
        // i18n
        'tr',
        // Source / media / display helpers
        'generatorSources', 'orderedSources', 'mediaKindForRef',
        'sanitizeVideoNodeProviderModel', 'videoProviderOptions',
        'videoModelOptions', 'providerVideoModels',
        'renderVideoImageInputs', 'renderPromptPreview',
        // Lifecycle / composition
        'scheduleSave', 'runCanvasGenerate',
        'bindCascadeButtons', 'cascadeBtnHtml', 'retryBarHtml',
        'render', 'showErrorModal',
        // Cloud upload + manual URL actions
        'uploadCanvasVideosToCloud', 'setCanvasManualVideoUrl',
        // Page-side DOM helper (called by renderVideoBody inline)
        'refreshIcons'
    ];

    function create(host) {
        if (!host || typeof host !== 'object') {
            throw new TypeError('WorkbenchCanvasClassicVideoCardBody.create: host must be an object');
        }
        for (var i = 0; i < REQUIRED_OPS.length; i++) {
            var name = REQUIRED_OPS[i];
            if (host[name] === undefined) {
                throw new TypeError('WorkbenchCanvasClassicVideoCardBody.create: missing required host op "' + name + '"');
            }
        }

        var document = host.document;
        var tr = host.tr;
        var generatorSources = host.generatorSources;
        var orderedSources = host.orderedSources;
        var mediaKindForRef = host.mediaKindForRef;
        var sanitizeVideoNodeProviderModel = host.sanitizeVideoNodeProviderModel;
        var videoProviderOptions = host.videoProviderOptions;
        var videoModelOptions = host.videoModelOptions;
        var providerVideoModels = host.providerVideoModels;
        var renderVideoImageInputs = host.renderVideoImageInputs;
        var renderPromptPreview = host.renderPromptPreview;
        var scheduleSave = host.scheduleSave;
        var runCanvasGenerate = host.runCanvasGenerate;
        var bindCascadeButtons = host.bindCascadeButtons;
        var cascadeBtnHtml = host.cascadeBtnHtml;
        var retryBarHtml = host.retryBarHtml;
        var render = host.render;
        var showErrorModal = host.showErrorModal;
        var uploadCanvasVideosToCloud = host.uploadCanvasVideosToCloud;
        var setCanvasManualVideoUrl = host.setCanvasManualVideoUrl;
        var refreshIcons = host.refreshIcons;

        function renderVideoBody(node) {
            var wrap = document.createElement('div');
            wrap.className = 'generator-body';
            var inputSources = generatorSources(node);
            var ordered = orderedSources(node, inputSources);
            var mediaInputs = ordered.filter(function (src) {
                return src.refs && src.refs.some(function (ref) {
                    return ['image', 'video', 'audio'].indexOf(mediaKindForRef(ref)) !== -1;
                });
            });
            var promptInputs = ordered.filter(function (src) {
                return src.prompt && (!src.refs || !src.refs.length);
            });
            sanitizeVideoNodeProviderModel(node);
            node.model = node.model || 'veo3-fast';
            wrap.innerHTML = ''
                + '<div class="prompt-list mb-3"></div>'
                + '<div class="video-input-head">'
                +   '<div class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Media</div>'
                +   '<div class="video-input-actions">'
                +     '<button type="button" class="tool-btn" data-video-manual-url title="手动输入视频 URL"><i data-lucide="link" class="w-4 h-4"></i><span>输入网址</span></button>'
                +     '<button type="button" class="tool-btn" data-video-temp-sh ' + (node.tempShUploading ? 'disabled' : '') + ' title="上传当前输入视频到云端直链"><i data-lucide="upload-cloud" class="w-4 h-4"></i><span>' + (node.tempShUploading ? '上传中...' : '上传云端') + '</span></button>'
                +   '</div>'
                + '</div>'
                + '<div class="input-list video-img-list"></div>'
                + '<div class="gen-settings">'
                +   '<div class="gen-settings-row">'
                +     '<select class="select-lite video-provider" style="flex:1">' + videoProviderOptions(node.apiProvider) + '</select>'
                +     '<select class="select-lite video-model" style="flex:2">' + videoModelOptions(node.model, node.apiProvider) + '</select>'
                +   '</div>'
                +   '<div class="gen-settings-row">'
                +     '<label class="field" style="flex:1">'
                +       '<div class="setting-title">' + tr('canvas.videoDuration') + '</div>'
                +       '<input class="setting-input video-duration" type="number" min="1" max="60" step="1" value="' + Number(node.duration || 5) + '">'
                +     '</label>'
                +     '<label class="field" style="flex:1">'
                +       '<div class="setting-title">' + tr('canvas.videoAspect') + '</div>'
                +       '<select class="select-lite video-aspect compact-select">'
                +         '<option value="16:9">16:9</option>'
                +         '<option value="9:16">9:16</option>'
                +         '<option value="1:1">1:1</option>'
                +         '<option value="4:3">4:3</option>'
                +         '<option value="3:4">3:4</option>'
                +         '<option value="21:9">21:9</option>'
                +         '<option value="9:21">9:21</option>'
                +         '<option value="keep_ratio">keep</option>'
                +         '<option value="adaptive">adapt</option>'
                +       '</select>'
                +     '</label>'
                +     '<label class="field" style="flex:1">'
                +       '<div class="setting-title">' + tr('canvas.videoResolution') + '</div>'
                +       '<select class="select-lite video-resolution compact-select">'
                +         '<option value="">Auto</option>'
                +         '<option value="480p">480p</option>'
                +         '<option value="720p">720p</option>'
                +         '<option value="1080p">1080p</option>'
                +         '<option value="780P">780P</option>'
                +       '</select>'
                +     '</label>'
                +   '</div>'
                +   '<div class="gen-settings-row" style="flex-wrap:wrap">'
                +     '<button type="button" class="setting-check ' + (node.enhancePrompt ? 'active' : '') + '" data-video-toggle="enhancePrompt"><span class="check-dot"></span>' + tr('canvas.videoEnhancePrompt') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.enableUpsample ? 'active' : '') + '" data-video-toggle="enableUpsample"><span class="check-dot"></span>' + tr('canvas.videoUpsample') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.watermark ? 'active' : '') + '" data-video-toggle="watermark"><span class="check-dot"></span>' + tr('canvas.videoWatermark') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.cameraFixed ? 'active' : '') + '" data-video-toggle="cameraFixed"><span class="check-dot"></span>' + tr('canvas.videoCameraFixed') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.generateAudio ? 'active' : '') + '" data-video-toggle="generateAudio"><span class="check-dot"></span>' + tr('canvas.videoGenerateAudio') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.multimodal ? 'active' : '') + '" data-video-toggle="multimodal"><span class="check-dot"></span>' + tr('canvas.videoMultimodal') + '</button>'
                +     '<button type="button" class="setting-check ' + (node.useFrameRoles ? 'active' : '') + '" data-video-toggle="useFrameRoles"><span class="check-dot"></span>' + tr('canvas.videoFirstLastFrames') + '</button>'
                +   '</div>'
                + '</div>'
                + '<div class="gen-run-row">'
                +   '<button class="gen-btn ' + (node.running ? 'running' : '') + '" ' + (node.running ? 'disabled' : '') + '><i data-lucide="clapperboard" class="w-4 h-4"></i>' + (node.running ? tr('canvas.generating') : tr('canvas.videoGenerate')) + '</button>'
                +   cascadeBtnHtml(node)
                + '</div>'
                + retryBarHtml(node);
            var providerSelect = wrap.querySelector('.video-provider');
            var modelSelect = wrap.querySelector('.video-model');
            var durationSelect = wrap.querySelector('.video-duration');
            var aspectSelect = wrap.querySelector('.video-aspect');
            var resolutionSelect = wrap.querySelector('.video-resolution');
            providerSelect.value = node.apiProvider;
            durationSelect.value = String(node.duration || 5);
            aspectSelect.value = node.aspectRatio || '16:9';
            resolutionSelect.value = node.resolution || '';
            [providerSelect, modelSelect, durationSelect, aspectSelect, resolutionSelect].forEach(function (input) {
                input.onmousedown = function (e) { e.stopPropagation(); };
                input.onclick = function (e) { e.stopPropagation(); };
            });
            providerSelect.onchange = function (e) {
                e.stopPropagation();
                node.apiProvider = e.target.value;
                var models = providerVideoModels(node.apiProvider);
                if (models.indexOf(node.model) === -1) node.model = models[0] || node.model;
                modelSelect.innerHTML = videoModelOptions(node.model, node.apiProvider);
                scheduleSave();
            };
            modelSelect.onchange = function (e) {
                e.stopPropagation();
                node.model = e.target.value;
                scheduleSave();
            };
            durationSelect.oninput = function (e) {
                e.stopPropagation();
                node.duration = Math.max(1, Math.min(60, Number(e.target.value || 5)));
                scheduleSave();
            };
            durationSelect.onblur = function (e) {
                e.target.value = String(Math.max(1, Math.min(60, Number(node.duration || 5))));
            };
            aspectSelect.onchange = function (e) {
                e.stopPropagation();
                node.aspectRatio = e.target.value;
                scheduleSave();
            };
            resolutionSelect.onchange = function (e) {
                e.stopPropagation();
                node.resolution = e.target.value;
                scheduleSave();
            };
            wrap.querySelectorAll('[data-video-toggle]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = function (e) {
                    e.stopPropagation();
                    var field = btn.dataset.videoToggle;
                    node[field] = !node[field];
                    if (field === 'multimodal' && node.multimodal) node.useFrameRoles = false;
                    if (field === 'useFrameRoles' && node.useFrameRoles) node.multimodal = false;
                    render();
                    scheduleSave();
                };
            });
            wrap.querySelectorAll('[data-video-temp-sh]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = async function (e) {
                    e.stopPropagation();
                    try {
                        await uploadCanvasVideosToCloud(node.id);
                    } catch (err) {
                        showErrorModal(err.message || '云端上传失败', '上传云端');
                    }
                };
            });
            wrap.querySelectorAll('[data-video-manual-url]').forEach(function (btn) {
                btn.onmousedown = function (e) { e.stopPropagation(); };
                btn.onclick = async function (e) {
                    e.stopPropagation();
                    try {
                        await setCanvasManualVideoUrl(node.id);
                    } catch (err) {
                        showErrorModal(err.message || '设置视频网址失败', '输入网址');
                    }
                };
            });
            var list = wrap.querySelector('.video-img-list');
            renderVideoImageInputs(list, node, mediaInputs);
            renderPromptPreview(wrap.querySelector('.prompt-list'), promptInputs);
            wrap.querySelector('.gen-btn').onclick = function (e) {
                e.stopPropagation();
                runCanvasGenerate(node.id);
            };
            bindCascadeButtons(wrap, node.id);
            if (refreshIcons) refreshIcons();
            return wrap;
        }

        return Object.freeze({
            renderBody: function (arg) { return renderVideoBody(arg.node); }
        });
    }

    if (typeof window !== 'undefined') {
        window.WorkbenchCanvasClassicVideoCardBody = Object.freeze({ create: create });
    }
})();