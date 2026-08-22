/* ============================================================
   环境学子雷达 - 前端脚本
   ============================================================ */

(function () {
    'use strict';

    // 全局状态
    const state = {
        latestData: null,
        historyData: [],
        expanded: false,
        trendChart: null,
        keywordChart: null,
        currentKeyword: null,
        glossaryData: [],
        glossaryMap: {},
        glossaryCategory: 'all',
        recommendedTerms: [],
        savedHotspots: [],
        // v4.1 新增
        dailyWordHistory: [],
        learningData: [],
        timelineChart: null,
        currentTimelineKeyword: null,
    };

    // 默认主题配置
    const defaultTheme = {
        primaryColor: '#10B981',
        bgColor: '#F9FAFB',
        borderRadius: 12,
        cardPadding: 16,
        fontSize: 16,
        dark: false,
    };

    // DOM 元素引用
    const els = {};

    // ============================================================
    // 初始化
    // ============================================================
    function init() {
        cacheElements();
        loadTheme();
        loadSavedHotspots();
        bindEvents();
        loadData();
    }

    function cacheElements() {
        els.loading = document.getElementById('loading');
        els.errorContainer = document.getElementById('errorContainer');
        els.cardList = document.getElementById('cardList');
        els.loadMoreContainer = document.getElementById('loadMoreContainer');
        els.loadMoreBtn = document.getElementById('loadMoreBtn');
        els.itemCount = document.getElementById('itemCount');
        els.summarySection = document.getElementById('summarySection');
        els.summaryText = document.getElementById('summaryText');
        els.tagCloud = document.getElementById('tagCloud');
        els.searchInput = document.getElementById('searchInput');
        els.themeToggle = document.getElementById('themeToggle');
        els.customizeBtn = document.getElementById('customizeBtn');
        els.customizePanel = document.getElementById('customizePanel');
        els.panelOverlay = document.getElementById('panelOverlay');
        els.panelClose = document.getElementById('panelClose');
        els.primaryColorPicker = document.getElementById('primaryColorPicker');
        els.bgColorPicker = document.getElementById('bgColorPicker');
        els.radiusSlider = document.getElementById('radiusSlider');
        els.radiusValue = document.getElementById('radiusValue');
        els.fontSizeSlider = document.getElementById('fontSizeSlider');
        els.fontSizeValue = document.getElementById('fontSizeValue');
        els.resetThemeBtn = document.getElementById('resetThemeBtn');
        els.keywordModal = document.getElementById('keywordModal');
        els.keywordOverlay = document.getElementById('keywordOverlay');
        els.keywordClose = document.getElementById('keywordClose');
        els.keywordModalTitle = document.getElementById('keywordModalTitle');
        els.algoLink = document.getElementById('algoLink');
        els.algoModal = document.getElementById('algoModal');
        els.algoOverlay = document.getElementById('algoOverlay');
        els.algoClose = document.getElementById('algoClose');
        els.aboutLink = document.getElementById('aboutLink');
        els.aboutModal = document.getElementById('aboutModal');
        els.aboutOverlay = document.getElementById('aboutOverlay');
        els.aboutClose = document.getElementById('aboutClose');
        els.toast = document.getElementById('toast');
        els.historyBtn = document.getElementById('historyBtn');
        els.historyModal = document.getElementById('historyModal');
        els.historyOverlay = document.getElementById('historyOverlay');
        els.historyClose = document.getElementById('historyClose');
        els.historyYear = document.getElementById('historyYear');
        els.historyMonth = document.getElementById('historyMonth');
        els.historyViewBtn = document.getElementById('historyViewBtn');
        els.historyDateInput = document.getElementById('historyDateInput');
        els.historyContent = document.getElementById('historyContent');
        els.glossaryBtn = document.getElementById('glossaryBtn');
        els.glossaryModal = document.getElementById('glossaryModal');
        els.glossaryOverlay = document.getElementById('glossaryOverlay');
        els.glossaryClose = document.getElementById('glossaryClose');
        els.glossarySearch = document.getElementById('glossary-search');
        els.glossaryRecommend = document.getElementById('glossaryRecommend');
        els.glossaryRecommendTags = document.getElementById('glossaryRecommendTags');
        els.glossaryRefreshBtn = document.getElementById('glossaryRefreshBtn');
        els.glossaryCategories = document.getElementById('glossary-categories');
        els.glossaryList = document.getElementById('glossary-list');
        els.termModal = document.getElementById('termModal');
        els.termOverlay = document.getElementById('termOverlay');
        els.termClose = document.getElementById('termClose');
        els.termModalTitle = document.getElementById('termModalTitle');
        els.termCategory = document.getElementById('termCategory');
        els.termDefinition = document.getElementById('termDefinition');
        els.termCopyBtn = document.getElementById('termCopyBtn');
        els.termTrendBtn = document.getElementById('termTrendBtn');
        els.currentTerm = null;
        // 收藏榜
        els.savedBtn = document.getElementById('savedBtn');
        els.savedModal = document.getElementById('savedModal');
        els.savedOverlay = document.getElementById('savedOverlay');
        els.savedClose = document.getElementById('savedClose');
        els.savedList = document.getElementById('savedList');
        // 知识库搜索建议
        els.glossarySuggestions = document.getElementById('glossarySuggestions');
        // 每日一词
        els.dailyWordSection = document.getElementById('dailyWordSection');
        els.dailyWordTerm = document.getElementById('dailyWordTerm');
        els.dailyWordDefinition = document.getElementById('dailyWordDefinition');
        els.dailyWordCategory = document.getElementById('dailyWordCategory');
        els.dailyWordRefresh = document.getElementById('dailyWordRefresh');
        // 学习路径
        els.learningBtn = document.getElementById('learningBtn');
        els.learningModal = document.getElementById('learningModal');
        els.learningOverlay = document.getElementById('learningOverlay');
        els.learningClose = document.getElementById('learningClose');
        els.learningList = document.getElementById('learningList');
        // 事件时间线
        els.timelineBtn = document.getElementById('timelineBtn');
        els.timelineModal = document.getElementById('timelineModal');
        els.timelineOverlay = document.getElementById('timelineOverlay');
        els.timelineClose = document.getElementById('timelineClose');
        els.timelineKeyword = document.getElementById('timelineKeyword');
        els.timelineLoadBtn = document.getElementById('timelineLoadBtn');
        els.timelineChart = document.getElementById('timelineChart');
        els.timelineInfo = document.getElementById('timelineInfo');
    }

    /**
     * 安全绑定事件：元素为 null 时跳过，避免脚本中断
     */
    function on(element, event, handler) {
        if (element && typeof element.addEventListener === 'function') {
            element.addEventListener(event, handler);
        }
    }

    function bindEvents() {
        // 搜索
        on(els.searchInput, 'input', handleSearch);

        // 暗黑模式
        on(els.themeToggle, 'click', toggleDarkMode);

        // 主题定制面板
        on(els.customizeBtn, 'click', openCustomizePanel);
        on(els.panelClose, 'click', closeCustomizePanel);
        on(els.panelOverlay, 'click', closeCustomizePanel);

        on(els.primaryColorPicker, 'input', (e) => {
            setCSSVar('--primary-color', e.target.value);
            saveTheme();
        });
        on(els.bgColorPicker, 'input', (e) => {
            setCSSVar('--bg-color', e.target.value);
            saveTheme();
        });
        on(els.radiusSlider, 'input', (e) => {
            const val = e.target.value;
            if (els.radiusValue) els.radiusValue.textContent = val;
            setCSSVar('--border-radius', val + 'px');
            saveTheme();
        });
        on(els.fontSizeSlider, 'input', (e) => {
            const val = e.target.value;
            if (els.fontSizeValue) els.fontSizeValue.textContent = val;
            setCSSVar('--font-size', val + 'px');
            saveTheme();
        });

        // 密度单选
        document.querySelectorAll('input[name="density"]').forEach((radio) => {
            radio.addEventListener('change', (e) => {
                setCSSVar('--card-padding', e.target.value + 'px');
                saveTheme();
            });
        });

        on(els.resetThemeBtn, 'click', resetTheme);

        // 查看全部
        on(els.loadMoreBtn, 'click', toggleExpand);

        // 关键词曲线模态框
        on(els.keywordOverlay, 'click', () => closeModal(els.keywordModal));
        on(els.keywordClose, 'click', () => closeModal(els.keywordModal));

        // 算法说明
        on(els.algoLink, 'click', (e) => {
            e.preventDefault();
            openModal(els.algoModal);
        });
        on(els.algoOverlay, 'click', () => closeModal(els.algoModal));
        on(els.algoClose, 'click', () => closeModal(els.algoModal));

        // 关于
        on(els.aboutLink, 'click', (e) => {
            e.preventDefault();
            openModal(els.aboutModal);
        });
        on(els.aboutOverlay, 'click', () => closeModal(els.aboutModal));
        on(els.aboutClose, 'click', () => closeModal(els.aboutModal));

        // 历史归档
        on(els.historyBtn, 'click', openHistoryModal);
        on(els.historyOverlay, 'click', () => closeModal(els.historyModal));
        on(els.historyClose, 'click', () => closeModal(els.historyModal));
        on(els.historyViewBtn, 'click', () => {
            if (els.historyYear && els.historyMonth) {
                const year = els.historyYear.value;
                const month = els.historyMonth.value;
                loadArchiveData(year, month);
            }
        });
        on(els.historyDateInput, 'change', (e) => {
            if (e.target.value) {
                loadDailyReport(e.target.value);
            }
        });

        // 知识库
        on(els.glossaryBtn, 'click', openGlossaryModal);
        on(els.glossaryOverlay, 'click', () => closeModal(els.glossaryModal));
        on(els.glossaryClose, 'click', () => closeModal(els.glossaryModal));
        on(els.glossarySearch, 'input', renderGlossaryList);
        on(els.glossaryRefreshBtn, 'click', () => {
            generateRecommendedTerms();
            renderRecommendedTerms();
        });

        // 收藏榜
        on(els.savedBtn, 'click', openSavedModal);
        on(els.savedOverlay, 'click', () => closeModal(els.savedModal));
        on(els.savedClose, 'click', () => closeModal(els.savedModal));

        // 知识库搜索建议
        on(els.glossarySearch, 'input', handleGlossarySearchInput);
        on(els.glossarySearch, 'focus', handleGlossarySearchInput);
        document.addEventListener('click', (e) => {
            if (els.glossarySuggestions && !e.target.closest('.glossary-search-box')) {
                els.glossarySuggestions.style.display = 'none';
            }
        });

        // 术语解释模态框
        on(els.termOverlay, 'click', () => closeModal(els.termModal));
        on(els.termClose, 'click', () => closeModal(els.termModal));
        on(els.termCopyBtn, 'click', () => {
            if (els.currentTerm) { copyToClipboard(els.currentTerm); }
        });
        on(els.termTrendBtn, 'click', () => {
            if (els.currentTerm) {
                closeModal(els.termModal);
                openKeywordChart(els.currentTerm);
            }
        });

        // 每日一词
        on(els.dailyWordRefresh, 'click', refreshDailyWord);

        // 学习路径模态框
        on(els.learningBtn, 'click', openLearningModal);
        on(els.learningOverlay, 'click', () => closeModal(els.learningModal));
        on(els.learningClose, 'click', () => closeModal(els.learningModal));

        // 事件时间线模态框
        on(els.timelineBtn, 'click', openTimelineModal);
        on(els.timelineOverlay, 'click', () => closeModal(els.timelineModal));
        on(els.timelineClose, 'click', () => closeModal(els.timelineModal));
        on(els.timelineLoadBtn, 'click', loadTimelineData);

        // ESC 关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAllModals();
                closeCustomizePanel();
            }
        });
    }

    // ============================================================
    // 数据加载
    // ============================================================
    async function loadData() {
        try {
            const [latestRes, historyRes, glossaryRes] = await Promise.all([
                fetch('data/latest.json'),
                fetch('data/history.json'),
                fetch('data/glossary.json'),
            ]);

            // 加载 latest.json（必需，失败则显示错误）
            if (!latestRes.ok) {
                throw new Error('latest.json 加载失败：' + latestRes.status);
            }
            try {
                state.latestData = await latestRes.json();
            } catch (e) {
                console.error('latest.json 解析失败：', e);
                throw new Error('latest.json 格式错误，请检查后端生成');
            }

            // 加载 history.json（可选，失败不影响主功能）
            if (historyRes.ok) {
                try {
                    state.historyData = await historyRes.json();
                } catch (e) {
                    console.warn('history.json 解析失败，跳过：', e);
                    state.historyData = [];
                }
            }

            // 加载 glossary.json（可选，失败不影响主功能）
            if (glossaryRes.ok) {
                try {
                    state.glossaryData = await glossaryRes.json();
                    if (Array.isArray(state.glossaryData)) {
                        state.glossaryData.forEach((item) => {
                            if (item && item.term) {
                                state.glossaryMap[item.term] = item;
                            }
                        });
                    }
                } catch (e) {
                    console.warn('glossary.json 解析失败，跳过：', e);
                    state.glossaryData = [];
                }
            }

            els.loading.style.display = 'none';
            renderAll();
            initDailyWord();
        } catch (err) {
            console.error('数据加载失败：', err);
            els.loading.style.display = 'none';
            els.errorContainer.style.display = 'flex';
        }
    }

    function renderAll() {
        renderSummary();
        renderCards();
        renderTagCloud();
        renderTrendChart();
    }

    // ============================================================
    // 渲染热点总结
    // ============================================================
    function renderSummary() {
        if (!state.latestData || !state.latestData.hot_summary) return;
        els.summarySection.style.display = 'block';
        els.summaryText.textContent = state.latestData.hot_summary;
    }

    // ============================================================
    // 渲染卡片列表
    // ============================================================
    function renderCards(filterText = '') {
        if (!state.latestData || !state.latestData.items) return;

        const items = state.latestData.items;
        const total = items.length;

        // 搜索过滤
        let filtered = items;
        if (filterText) {
            const lower = filterText.toLowerCase();
            filtered = items.filter((item) => {
                const title = (item.title || '').toLowerCase();
                const summary = (item.summary || '').toLowerCase();
                const source = (item.source || '').toLowerCase();
                const keywords = item.matched_keywords || [];
                return (
                    title.includes(lower) ||
                    summary.includes(lower) ||
                    source.includes(lower) ||
                    keywords.some((k) => (k || '').toLowerCase().includes(lower))
                );
            });
        }

        // 显示数量
        const showCount = state.expanded ? filtered.length : Math.min(10, filtered.length);

        els.cardList.innerHTML = '';

        if (filtered.length === 0) {
            els.cardList.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:var(--text-secondary);padding:32px;">没有找到匹配的热点</p>';
            els.loadMoreContainer.style.display = 'none';
            els.itemCount.textContent = `共 ${total} 条`;
            return;
        }

        for (let i = 0; i < showCount; i++) {
            const item = filtered[i];
            const card = createCard(item, i + 1);
            els.cardList.appendChild(card);
        }

        // 查看全部按钮
        if (!filterText && total > 10) {
            els.loadMoreContainer.style.display = 'block';
            els.loadMoreBtn.textContent = state.expanded ? '收起' : `查看全部（共 ${total} 条）`;
        } else {
            els.loadMoreContainer.style.display = 'none';
        }

        els.itemCount.textContent = `共 ${total} 条`;
    }

    function createCard(item, rank) {
        const card = document.createElement('div');
        card.className = 'hotspot-card';
        card.dataset.expanded = 'false';

        // 排名
        const rankClass = rank <= 3 ? `rank-${rank}` : 'rank-other';
        const rankEl = document.createElement('div');
        rankEl.className = `card-rank ${rankClass}`;
        rankEl.textContent = rank;
        card.appendChild(rankEl);

        // 头部：标题 + 分享
        const header = document.createElement('div');
        header.className = 'card-header';

        const titleEl = document.createElement('h3');
        titleEl.className = 'card-title clickable';
        titleEl.textContent = item.title || '无标题';
        titleEl.title = '点击展开摘要';
        titleEl.addEventListener('click', () => toggleCardSummary(card, item));
        header.appendChild(titleEl);

        const shareBtn = document.createElement('button');
        shareBtn.className = 'share-btn';
        shareBtn.title = '分享';
        shareBtn.innerHTML = '🔗';
        shareBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleShare(item);
        });
        header.appendChild(shareBtn);

        // 收藏按钮
        const saveBtn = document.createElement('button');
        const isSaved = isHotspotSaved(item);
        saveBtn.className = 'card-save-btn' + (isSaved ? ' saved' : '');
        saveBtn.innerHTML = isSaved ? '★' : '☆';
        saveBtn.title = isSaved ? '取消收藏' : '收藏';
        saveBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleHotspotSave(item, saveBtn);
        });
        header.appendChild(saveBtn);

        card.appendChild(header);

        // 元信息
        const meta = document.createElement('div');
        meta.className = 'card-meta';

        const sourceBadge = document.createElement('span');
        sourceBadge.className = 'source-badge';
        sourceBadge.textContent = item.source || '未知';
        meta.appendChild(sourceBadge);

        const timeEl = document.createElement('span');
        timeEl.className = 'card-time';
        timeEl.textContent = formatRelativeTime(item.published);
        meta.appendChild(timeEl);

        const hotnessEl = document.createElement('span');
        const hotness = item.hotness || 0;
        let hotnessClass = 'hotness-low';
        if (hotness >= 20) hotnessClass = 'hotness-high';
        else if (hotness >= 12) hotnessClass = 'hotness-medium';
        hotnessEl.className = `hotness-badge ${hotnessClass}`;
        hotnessEl.innerHTML = `🔥 ${hotness}`;
        meta.appendChild(hotnessEl);

        card.appendChild(meta);

        // 摘要（每个卡片都显示，为空则提示）
        const summaryText = item.summary && item.summary.trim() ? item.summary.trim() : '';
        const summaryEl = document.createElement('p');
        if (summaryText) {
            summaryEl.className = 'card-summary';
            summaryEl.textContent = summaryText;
            summaryEl.title = '点击展开完整摘要';
        } else {
            summaryEl.className = 'card-summary empty-summary';
            summaryEl.textContent = '暂无摘要，点击查看详情';
        }
        summaryEl.addEventListener('click', () => toggleCardSummary(card, item));
        card.appendChild(summaryEl);

        // 分析文字
        const analysisText = item.analysis || '';
        if (analysisText) {
            const analysisEl = document.createElement('div');
            analysisEl.className = 'card-analysis';
            analysisEl.textContent = analysisText;
            card.appendChild(analysisEl);
        }

        // 摘要详情区域（展开时显示）
        const detailEl = document.createElement('div');
        detailEl.className = 'card-detail';

        const detailText = document.createElement('div');
        detailText.className = 'card-detail-text';
        detailText.textContent = summaryText || '暂无摘要内容，请点击"阅读原文"查看完整内容。';
        detailEl.appendChild(detailText);

        const detailActions = document.createElement('div');
        detailActions.className = 'card-detail-actions';

        const readOriginalBtn = document.createElement('a');
        readOriginalBtn.className = 'read-original-btn';
        readOriginalBtn.href = item.link || '#';
        readOriginalBtn.target = '_blank';
        readOriginalBtn.rel = 'noopener noreferrer';
        readOriginalBtn.innerHTML = '📖 阅读原文';
        detailActions.appendChild(readOriginalBtn);

        // 代理访问按钮
        if (item.link) {
            const proxyBtn = document.createElement('a');
            proxyBtn.className = 'proxy-btn';
            proxyBtn.href = 'https://translate.google.com/translate?hl=zh-CN&sl=auto&tl=zh-CN&u=' + encodeURIComponent(item.link);
            proxyBtn.target = '_blank';
            proxyBtn.rel = 'noopener noreferrer';
            proxyBtn.innerHTML = '🌐 代理访问';
            detailActions.appendChild(proxyBtn);
        }

        const collapseBtn = document.createElement('button');
        collapseBtn.className = 'collapse-btn';
        collapseBtn.innerHTML = '收起 ▲';
        collapseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleCardSummary(card, item);
        });
        detailActions.appendChild(collapseBtn);

        detailEl.appendChild(detailActions);
        card.appendChild(detailEl);

        // 关键词标签
        if (item.matched_keywords && item.matched_keywords.length > 0) {
            const tagsEl = document.createElement('div');
            tagsEl.className = 'card-tags';
            item.matched_keywords.forEach((kw) => {
                const tag = document.createElement('span');
                const inGlossary = state.glossaryMap[kw];
                tag.className = inGlossary ? 'keyword-tag glossary-term' : 'keyword-tag';
                tag.textContent = kw;
                if (inGlossary) {
                    tag.addEventListener('click', (e) => {
                        e.stopPropagation();
                        openTermModal(kw);
                    });
                } else {
                    tag.addEventListener('click', (e) => {
                        e.stopPropagation();
                        openKeywordChart(kw);
                    });
                }
                tagsEl.appendChild(tag);
            });
            card.appendChild(tagsEl);
        }

        return card;
    }

    /**
     * 切换卡片摘要的展开/收起状态
     */
    function toggleCardSummary(card, item) {
        const isExpanded = card.dataset.expanded === 'true';
        const summaryEl = card.querySelector('.card-summary');
        const detailEl = card.querySelector('.card-detail');

        if (isExpanded) {
            // 收起
            card.dataset.expanded = 'false';
            if (summaryEl) {
                summaryEl.classList.remove('expanded');
            }
            if (detailEl) {
                detailEl.classList.remove('show');
            }
        } else {
            // 展开
            card.dataset.expanded = 'true';
            if (summaryEl) {
                summaryEl.classList.add('expanded');
            }
            if (detailEl) {
                detailEl.classList.add('show');
            }
            // 滚动到可视区域
            setTimeout(() => {
                detailEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        }
    }

    // ============================================================
    // 收藏功能
    // ============================================================
    function loadSavedHotspots() {
        try {
            const data = localStorage.getItem('saved_hotspots');
            state.savedHotspots = data ? JSON.parse(data) : [];
        } catch (e) {
            state.savedHotspots = [];
        }
    }

    function saveSavedHotspots() {
        try {
            localStorage.setItem('saved_hotspots', JSON.stringify(state.savedHotspots));
        } catch (e) {
            console.error('保存收藏失败：', e);
        }
    }

    function isHotspotSaved(item) {
        return state.savedHotspots.some((s) => s.link === item.link);
    }

    function toggleHotspotSave(item, btnEl) {
        const index = state.savedHotspots.findIndex((s) => s.link === item.link);
        if (index >= 0) {
            // 取消收藏
            state.savedHotspots.splice(index, 1);
            if (btnEl) {
                btnEl.classList.remove('saved');
                btnEl.innerHTML = '☆';
                btnEl.title = '收藏';
            }
            showToast('已取消收藏');
        } else {
            // 添加收藏
            const savedItem = {
                title: item.title,
                link: item.link,
                source: item.source,
                published: item.published,
                hotness: item.hotness,
                summary: item.summary,
                analysis: item.analysis,
                matched_keywords: item.matched_keywords,
                saved_at: new Date().toISOString(),
            };
            state.savedHotspots.push(savedItem);
            if (btnEl) {
                btnEl.classList.add('saved');
                btnEl.innerHTML = '★';
                btnEl.title = '取消收藏';
            }
            showToast('已收藏');
        }
        saveSavedHotspots();
    }

    function openSavedModal() {
        if (!els.savedModal) return;
        renderSavedList();
        els.savedModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function renderSavedList() {
        if (!els.savedList) return;
        if (state.savedHotspots.length === 0) {
            els.savedList.innerHTML = '<div class="saved-empty">暂无收藏，快去收藏你关心的热点吧！</div>';
            return;
        }

        // 按热度分数从高到低排序
        const sorted = [...state.savedHotspots].sort((a, b) => (b.hotness || 0) - (a.hotness || 0));

        els.savedList.innerHTML = '';
        sorted.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'saved-card';

            const rankEl = document.createElement('div');
            rankEl.className = 'saved-rank';
            rankEl.textContent = index + 1;
            card.appendChild(rankEl);

            const body = document.createElement('div');
            body.className = 'saved-body';

            const titleEl = document.createElement('div');
            titleEl.className = 'saved-title';
            titleEl.textContent = item.title || '无标题';
            titleEl.title = '点击展开详情';
            titleEl.addEventListener('click', () => {
                const detail = card.querySelector('.saved-detail');
                if (detail) {
                    detail.classList.toggle('show');
                }
            });
            body.appendChild(titleEl);

            const meta = document.createElement('div');
            meta.className = 'saved-meta';

            const sourceEl = document.createElement('span');
            sourceEl.className = 'saved-source';
            sourceEl.textContent = item.source || '未知';
            meta.appendChild(sourceEl);

            const hotnessEl = document.createElement('span');
            hotnessEl.className = 'saved-hotness';
            hotnessEl.textContent = '🔥 ' + (item.hotness || 0);
            meta.appendChild(hotnessEl);

            body.appendChild(meta);

            // 详情区域
            const detail = document.createElement('div');
            detail.className = 'saved-detail';

            const summaryEl = document.createElement('div');
            summaryEl.className = 'saved-summary';
            summaryEl.textContent = item.summary && item.summary.trim() ? item.summary.trim() : '暂无摘要内容。';
            detail.appendChild(summaryEl);

            if (item.analysis) {
                const analysisEl = document.createElement('div');
                analysisEl.className = 'saved-analysis';
                analysisEl.textContent = item.analysis;
                detail.appendChild(analysisEl);
            }

            const actions = document.createElement('div');
            actions.className = 'saved-detail-actions';

            if (item.link) {
                const readBtn = document.createElement('a');
                readBtn.className = 'read-original-btn';
                readBtn.href = item.link;
                readBtn.target = '_blank';
                readBtn.rel = 'noopener noreferrer';
                readBtn.innerHTML = '📖 阅读原文';
                actions.appendChild(readBtn);

                const proxyBtn = document.createElement('a');
                proxyBtn.className = 'proxy-btn';
                proxyBtn.href = 'https://translate.google.com/translate?hl=zh-CN&sl=auto&tl=zh-CN&u=' + encodeURIComponent(item.link);
                proxyBtn.target = '_blank';
                proxyBtn.rel = 'noopener noreferrer';
                proxyBtn.innerHTML = '🌐 代理访问';
                actions.appendChild(proxyBtn);
            }

            const removeBtn = document.createElement('button');
            removeBtn.className = 'saved-remove-btn';
            removeBtn.textContent = '取消收藏';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = state.savedHotspots.findIndex((s) => s.link === item.link);
                if (idx >= 0) {
                    state.savedHotspots.splice(idx, 1);
                    saveSavedHotspots();
                    renderSavedList();
                    // 同步更新主榜单的收藏按钮状态
                    renderCards(els.searchInput ? els.searchInput.value : '');
                    showToast('已取消收藏');
                }
            });
            actions.appendChild(removeBtn);

            detail.appendChild(actions);
            body.appendChild(detail);
            card.appendChild(body);
            els.savedList.appendChild(card);
        });
    }

    // ============================================================
    // 渲染关键词标签云
    // ============================================================
    function renderTagCloud() {
        if (!state.latestData || !state.latestData.keyword_analysis) return;

        const keywords = state.latestData.keyword_analysis;
        els.tagCloud.innerHTML = '';

        if (keywords.length === 0) {
            els.tagCloud.innerHTML = '<span style="color:var(--text-muted);">暂无关键词数据</span>';
            return;
        }

        const maxCount = Math.max(...keywords.map((k) => k.count));
        const minCount = Math.min(...keywords.map((k) => k.count));

        keywords.forEach((kw) => {
            const tag = document.createElement('span');
            tag.className = 'cloud-tag';
            tag.textContent = `${kw.keyword} (${kw.count})`;

            // 根据频次计算大小和颜色深浅
            const ratio = maxCount === minCount ? 1 : (kw.count - minCount) / (maxCount - minCount);
            const fontSize = 0.8 + ratio * 0.5;
            const opacity = 0.6 + ratio * 0.4;

            tag.style.fontSize = fontSize + 'rem';
            tag.style.backgroundColor = `rgba(16, 185, 129, ${0.1 + ratio * 0.15})`;
            tag.style.color = `rgba(5, 150, 105, ${opacity})`;
            tag.style.borderColor = `rgba(16, 185, 129, ${0.2 + ratio * 0.3})`;

            tag.addEventListener('click', () => openKeywordChart(kw.keyword));
            els.tagCloud.appendChild(tag);
        });
    }

    // ============================================================
    // 渲染近7天趋势图
    // ============================================================
    function renderTrendChart() {
        const chartEl = document.getElementById('trendChart');
        if (!chartEl) return;
        const ctx = chartEl.getContext('2d');
        if (!ctx) return;

        // 取最近7天数据（按日期升序）
        const historyData = Array.isArray(state.historyData) ? state.historyData : [];
        const recent7 = historyData.slice(0, 7).reverse();

        const labels = recent7.map((h) => h.date ? h.date.slice(5) : '');
        const data = recent7.map((h) => h.total_items || 0);

        if (state.trendChart) {
            state.trendChart.destroy();
        }

        const isDark = document.body.classList.contains('dark');
        const textColor = isDark ? '#94A3B8' : '#6B7280';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(107, 114, 128, 0.1)';

        state.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '资讯条数',
                    data: data,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10B981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1E293B' : '#1F2937',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: isDark ? '#334155' : '#374151',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                    },
                },
                scales: {
                    x: {
                        grid: {
                            color: gridColor,
                        },
                        ticks: {
                            color: textColor,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: gridColor,
                        },
                        ticks: {
                            color: textColor,
                            stepSize: 1,
                        },
                    },
                },
            },
        });
    }

    // ============================================================
    // 关键词历史曲线
    // ============================================================
    function openKeywordChart(keyword) {
        state.currentKeyword = keyword;
        els.keywordModalTitle.textContent = `📈 "${keyword}" 历史热度趋势`;
        openModal(els.keywordModal);

        // 延迟渲染，确保 canvas 可见
        setTimeout(() => renderKeywordChart(keyword), 100);
    }

    function renderKeywordChart(keyword) {
        const chartEl = document.getElementById('keywordChart');
        if (!chartEl) return;
        const ctx = chartEl.getContext('2d');
        if (!ctx) return;

        // 从历史数据中统计该关键词出现的情况
        // history.json 中每条记录有 keywords（前5关键词）
        // 我们用是否出现在前5中来近似表示热度
        const history = state.historyData.slice().reverse(); // 按日期升序

        const labels = [];
        const data = [];

        history.forEach((h) => {
            if (h.date) {
                labels.push(h.date.slice(5));
                // 如果该关键词在当日前5关键词中，记为1，否则0
                const inTop5 = h.keywords && h.keywords.includes(keyword) ? 1 : 0;
                data.push(inTop5);
            }
        });

        if (state.keywordChart) {
            state.keywordChart.destroy();
        }

        const isDark = document.body.classList.contains('dark');
        const textColor = isDark ? '#94A3B8' : '#6B7280';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(107, 114, 128, 0.1)';

        state.keywordChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `"${keyword}" 出现频次`,
                    data: data,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#10B981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1E293B' : '#1F2937',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: isDark ? '#334155' : '#374151',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                return context.raw === 1 ? '进入当日热门前5' : '未进入前5';
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {
                            color: gridColor,
                        },
                        ticks: {
                            color: textColor,
                            maxTicksLimit: 12,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        max: 1.2,
                        grid: {
                            color: gridColor,
                        },
                        ticks: {
                            color: textColor,
                            stepSize: 1,
                            callback: function (val) {
                                return val === 1 ? '热门' : '';
                            },
                        },
                    },
                },
            },
        });
    }

    // ============================================================
    // 分享功能
    // ============================================================
    function handleShare(item) {
        const title = item.title || '环境学子雷达热点';
        const url = item.link || window.location.href;

        if (navigator.share) {
            navigator.share({
                title: title,
                text: title,
                url: url,
            }).catch((err) => {
                if (err.name !== 'AbortError') {
                    console.error('分享失败：', err);
                    copyToClipboard(url);
                }
            });
        } else {
            copyToClipboard(url);
        }
    }

    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('链接已复制！');
            }).catch(() => {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showToast('链接已复制！');
        } catch (err) {
            showToast('复制失败，请手动复制');
        }
        document.body.removeChild(textarea);
    }

    // ============================================================
    // 搜索
    // ============================================================
    function handleSearch(e) {
        const text = e.target.value.trim();
        renderCards(text);
    }

    function toggleExpand() {
        state.expanded = !state.expanded;
        renderCards(els.searchInput.value.trim());
    }

    // ============================================================
    // ============================================================
    // 主题 & 暗黑模式
    // ============================================================
    function toggleDarkMode() {
        document.body.classList.toggle('dark');
        const isDark = document.body.classList.contains('dark');
        els.themeToggle.textContent = isDark ? '☀️' : '🌙';
        saveTheme();
        // 重新渲染图表以适配颜色
        if (state.trendChart) renderTrendChart();
    }

    function openCustomizePanel() {
        els.customizePanel.classList.add('open');
        els.panelOverlay.classList.add('show');
    }

    function closeCustomizePanel() {
        els.customizePanel.classList.remove('open');
        els.panelOverlay.classList.remove('show');
    }

    function setCSSVar(name, value) {
        document.documentElement.style.setProperty(name, value);
    }

    function loadTheme() {
        try {
            const saved = localStorage.getItem('radar-theme');
            if (saved) {
                const theme = JSON.parse(saved);
                applyTheme(theme);
            }
        } catch (err) {
            console.error('加载主题失败：', err);
        }
    }

    function applyTheme(theme) {
        if (theme.primaryColor) {
            setCSSVar('--primary-color', theme.primaryColor);
            els.primaryColorPicker.value = theme.primaryColor;
        }
        if (theme.bgColor) {
            setCSSVar('--bg-color', theme.bgColor);
            els.bgColorPicker.value = theme.bgColor;
        }
        if (theme.borderRadius !== undefined) {
            setCSSVar('--border-radius', theme.borderRadius + 'px');
            els.radiusSlider.value = theme.borderRadius;
            els.radiusValue.textContent = theme.borderRadius;
        }
        if (theme.cardPadding !== undefined) {
            setCSSVar('--card-padding', theme.cardPadding + 'px');
            document.querySelectorAll('input[name="density"]').forEach((radio) => {
                radio.checked = parseInt(radio.value) === theme.cardPadding;
            });
        }
        if (theme.fontSize !== undefined) {
            setCSSVar('--font-size', theme.fontSize + 'px');
            els.fontSizeSlider.value = theme.fontSize;
            els.fontSizeValue.textContent = theme.fontSize;
        }
        if (theme.dark) {
            document.body.classList.add('dark');
            els.themeToggle.textContent = '☀️';
        }
    }

    function saveTheme() {
        const theme = {
            primaryColor: els.primaryColorPicker.value,
            bgColor: els.bgColorPicker.value,
            borderRadius: parseInt(els.radiusSlider.value),
            cardPadding: parseInt(document.querySelector('input[name="density"]:checked').value),
            fontSize: parseInt(els.fontSizeSlider.value),
            dark: document.body.classList.contains('dark'),
        };
        try {
            localStorage.setItem('radar-theme', JSON.stringify(theme));
        } catch (err) {
            console.error('保存主题失败：', err);
        }
    }

    function resetTheme() {
        applyTheme(defaultTheme);
        document.body.classList.remove('dark');
        els.themeToggle.textContent = '🌙';
        saveTheme();
        if (state.trendChart) renderTrendChart();
        showToast('已恢复默认主题');
    }

    // ============================================================
    // 模态框工具
    // ============================================================
    // ============================================================
    // 环境知识库
    // ============================================================
    function openGlossaryModal() {
        openModal(els.glossaryModal);
        state.glossaryCategory = 'all';
        els.glossarySearch.value = '';
        generateRecommendedTerms();
        renderRecommendedTerms();
        renderGlossaryCategories();
        renderGlossaryList();
    }

    /**
     * 随机生成推荐词条（6-8个）
     */
    function generateRecommendedTerms() {
        if (!state.glossaryData || state.glossaryData.length === 0) {
            state.recommendedTerms = [];
            return;
        }
        const count = Math.min(state.glossaryData.length, 6 + Math.floor(Math.random() * 3)); // 6-8个
        const shuffled = [...state.glossaryData].sort(() => Math.random() - 0.5);
        state.recommendedTerms = shuffled.slice(0, count);
    }

    /**
     * 渲染推荐词条标签
     */
    function renderRecommendedTerms() {
        if (!els.glossaryRecommendTags) return;
        els.glossaryRecommendTags.innerHTML = '';

        if (!state.recommendedTerms || state.recommendedTerms.length === 0) {
            els.glossaryRecommendTags.innerHTML = '<span style="color:var(--text-muted);font-size:0.82rem;">暂无推荐词条</span>';
            return;
        }

        state.recommendedTerms.forEach((item) => {
            const tag = document.createElement('span');
            tag.className = 'glossary-recommend-tag';
            tag.textContent = item.term;
            tag.title = item.definition;
            tag.addEventListener('click', () => {
                // 填入搜索框并触发搜索
                els.glossarySearch.value = item.term;
                renderGlossaryList(item.term);
                // 高亮匹配的卡片
                setTimeout(() => {
                    const cards = els.glossaryList.querySelectorAll('.glossary-card');
                    cards.forEach((card) => {
                        const termEl = card.querySelector('.glossary-card-term');
                        if (termEl && termEl.textContent === item.term) {
                            card.classList.add('highlight');
                            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            setTimeout(() => card.classList.remove('highlight'), 2000);
                        }
                    });
                }, 100);
            });
            els.glossaryRecommendTags.appendChild(tag);
        });
    }

    function handleGlossarySearchInput() {
        const query = els.glossarySearch.value.trim().toLowerCase();
        if (!els.glossarySuggestions) return;

        if (!query) {
            els.glossarySuggestions.style.display = 'none';
            renderGlossaryList();
            return;
        }

        // 模糊匹配词条
        const matches = state.glossaryData.filter((item) => {
            return (
                item.term.toLowerCase().includes(query) ||
                item.definition.toLowerCase().includes(query)
            );
        }).slice(0, 8);

        if (matches.length === 0) {
            els.glossarySuggestions.innerHTML = '<div class="glossary-suggestion-empty">暂无匹配词条，可提交收录</div>';
        } else {
            els.glossarySuggestions.innerHTML = '';
            matches.forEach((item) => {
                const suggestion = document.createElement('div');
                suggestion.className = 'glossary-suggestion-item';
                suggestion.innerHTML = `
                    <span class="glossary-suggestion-term">${escapeHtml(item.term)}</span>
                    <span class="glossary-suggestion-cat">${escapeHtml(item.category)}</span>
                `;
                suggestion.addEventListener('click', () => {
                    els.glossarySearch.value = item.term;
                    els.glossarySuggestions.style.display = 'none';
                    renderGlossaryList(item.term);
                    // 高亮匹配卡片
                    setTimeout(() => {
                        const cards = els.glossaryList.querySelectorAll('.glossary-card');
                        cards.forEach((card) => {
                            const termEl = card.querySelector('.glossary-card-term');
                            if (termEl && termEl.textContent === item.term) {
                                card.classList.add('highlight');
                                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                setTimeout(() => card.classList.remove('highlight'), 2000);
                            }
                        });
                    }, 100);
                });
                els.glossarySuggestions.appendChild(suggestion);
            });
        }
        els.glossarySuggestions.style.display = 'block';
        renderGlossaryList(query);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function renderGlossaryCategories() {
        const categories = [...new Set(state.glossaryData.map(item => item.category))];
        categories.sort();
        els.glossaryCategories.innerHTML = '';

        const allBtn = document.createElement('button');
        allBtn.className = 'glossary-cat-btn' + (state.glossaryCategory === 'all' ? ' active' : '');
        allBtn.textContent = '全部';
        allBtn.addEventListener('click', () => {
            state.glossaryCategory = 'all';
            renderGlossaryCategories();
            renderGlossaryList();
        });
        els.glossaryCategories.appendChild(allBtn);

        categories.forEach((cat) => {
            const btn = document.createElement('button');
            btn.className = 'glossary-cat-btn' + (state.glossaryCategory === cat ? ' active' : '');
            btn.textContent = cat;
            btn.addEventListener('click', () => {
                state.glossaryCategory = cat;
                renderGlossaryCategories();
                renderGlossaryList();
            });
            els.glossaryCategories.appendChild(btn);
        });
    }

    function renderGlossaryList(searchTerm) {
        const searchText = (searchTerm !== undefined ? searchTerm : els.glossarySearch.value).trim().toLowerCase();
        let filtered = state.glossaryData;

        if (state.glossaryCategory !== 'all') {
            filtered = filtered.filter(item => item.category === state.glossaryCategory);
        }

        if (searchText) {
            filtered = filtered.filter(item =>
                item.term.toLowerCase().includes(searchText) ||
                item.definition.toLowerCase().includes(searchText)
            );
        }

        els.glossaryList.innerHTML = '';

        if (filtered.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'glossary-empty';
            empty.textContent = '未找到匹配的词条';
            els.glossaryList.appendChild(empty);
            return;
        }

        filtered.forEach((item) => {
            const card = document.createElement('div');
            card.className = 'glossary-card';

            const header = document.createElement('div');
            const termEl = document.createElement('span');
            termEl.className = 'glossary-card-term';
            termEl.textContent = item.term;
            termEl.addEventListener('click', () => {
                copyToClipboard(item.term);
            });
            header.appendChild(termEl);

            const catEl = document.createElement('span');
            catEl.className = 'glossary-card-cat';
            catEl.textContent = item.category;
            header.appendChild(catEl);

            const defEl = document.createElement('p');
            defEl.className = 'glossary-card-def';
            defEl.textContent = item.definition;

            card.appendChild(header);
            card.appendChild(defEl);
            els.glossaryList.appendChild(card);
        });
    }

    function openTermModal(term) {
        const item = state.glossaryMap[term];
        if (!item) {
            openKeywordChart(term);
            return;
        }
        els.currentTerm = term;
        els.termModalTitle.textContent = item.term;
        els.termCategory.textContent = item.category;
        els.termDefinition.textContent = item.definition;
        openModal(els.termModal);
    }

    function openModal(modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    function closeAllModals() {
        document.querySelectorAll('.modal.show').forEach((m) => {
            m.classList.remove('show');
        });
        document.body.style.overflow = '';
    }

    // ============================================================
    // 工具函数
    // ============================================================
    function formatRelativeTime(isoString) {
        if (!isoString) return '未知时间';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return '刚刚';
            if (diffMins < 60) return `${diffMins} 分钟前`;
            if (diffHours < 24) return `${diffHours} 小时前`;
            if (diffDays < 7) return `${diffDays} 天前`;
            return date.toLocaleDateString('zh-CN');
        } catch (err) {
            return '未知时间';
        }
    }

    function showToast(message) {
        els.toast.textContent = message;
        els.toast.classList.add('show');
        setTimeout(() => {
            els.toast.classList.remove('show');
        }, 2000);
    }

    // ============================================================
    // 历史归档
    // ============================================================
    function openHistoryModal() {
        openModal(els.historyModal);
        populateYearMonthSelects();
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        els.historyYear.value = year;
        els.historyMonth.value = month;
        loadArchiveData(year, month);
    }

    function populateYearMonthSelects() {
        const now = new Date();
        const currentYear = now.getFullYear();

        // 年份：从2024年到当前年+1
        els.historyYear.innerHTML = '';
        for (let y = 2024; y <= currentYear + 1; y++) {
            const opt = document.createElement('option');
            opt.value = y;
            opt.textContent = y + '年';
            els.historyYear.appendChild(opt);
        }

        // 月份：1-12
        els.historyMonth.innerHTML = '';
        for (let m = 1; m <= 12; m++) {
            const opt = document.createElement('option');
            const val = String(m).padStart(2, '0');
            opt.value = val;
            opt.textContent = m + '月';
            els.historyMonth.appendChild(opt);
        }
    }

    async function loadArchiveData(year, month) {
        const yearMonth = `${year}-${month}`;
        els.historyContent.innerHTML = '<div class="history-loading">正在加载归档数据...</div>';

        try {
            const response = await fetch(`data/archive/${yearMonth}.json`);
            if (!response.ok) {
                if (response.status === 404) {
                    els.historyContent.innerHTML = `<div class="history-empty">${yearMonth} 暂无归档数据</div>`;
                    return;
                }
                throw new Error('加载失败');
            }
            const data = await response.json();
            renderArchiveList(data, yearMonth);
        } catch (err) {
            console.error('归档数据加载失败：', err);
            els.historyContent.innerHTML = `<div class="history-error">归档数据加载失败，请稍后再试</div>`;
        }
    }

    function renderArchiveList(data, yearMonth) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            els.historyContent.innerHTML = `<div class="history-empty">${yearMonth} 暂无归档数据</div>`;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'archive-grid';

        data.forEach((record) => {
            const card = document.createElement('div');
            card.className = 'archive-day-card';
            card.addEventListener('click', () => loadDailyReport(record.date));

            const dateEl = document.createElement('div');
            dateEl.className = 'archive-day-date';
            dateEl.textContent = record.date ? record.date.slice(8) + '日' : '未知';

            const countEl = document.createElement('div');
            countEl.className = 'archive-day-count';
            countEl.textContent = `${record.total_items || 0} 条资讯`;

            const keywordsEl = document.createElement('div');
            keywordsEl.className = 'archive-day-keywords';
            if (record.keywords && record.keywords.length > 0) {
                record.keywords.slice(0, 3).forEach((kw) => {
                    const tag = document.createElement('span');
                    tag.className = 'archive-day-keyword';
                    tag.textContent = kw;
                    keywordsEl.appendChild(tag);
                });
            }

            card.appendChild(dateEl);
            card.appendChild(countEl);
            card.appendChild(keywordsEl);
            grid.appendChild(card);
        });

        els.historyContent.innerHTML = '';
        els.historyContent.appendChild(grid);
    }

    async function loadDailyReport(dateStr) {
        els.historyContent.innerHTML = '<div class="history-loading">正在加载当日报告...</div>';

        try {
            const response = await fetch(`data/daily/${dateStr}.json`);
            if (!response.ok) {
                if (response.status === 404) {
                    els.historyContent.innerHTML = `<div class="history-empty">${dateStr} 暂无数据</div>`;
                    return;
                }
                throw new Error('加载失败');
            }
            const data = await response.json();
            renderDailyTop10(data, dateStr);
        } catch (err) {
            console.error('当日报告加载失败：', err);
            els.historyContent.innerHTML = `<div class="history-error">数据加载失败，请稍后再试</div>`;
        }
    }

    function renderDailyTop10(data, dateStr) {
        const items = data.items || [];

        const header = document.createElement('div');
        header.className = 'history-top10-header';

        const title = document.createElement('div');
        title.className = 'history-top10-title';
        title.textContent = `📅 ${dateStr} 热点 TOP ${items.length}`;

        const backBtn = document.createElement('button');
        backBtn.className = 'history-back-btn';
        backBtn.textContent = '← 返回归档';
        backBtn.addEventListener('click', () => {
            const year = els.historyYear.value;
            const month = els.historyMonth.value;
            loadArchiveData(year, month);
        });

        header.appendChild(title);
        header.appendChild(backBtn);

        const list = document.createElement('div');
        list.className = 'history-card-list';

        items.forEach((item, index) => {
            const rank = index + 1;
            const card = document.createElement('div');
            card.className = 'history-card';

            const rankEl = document.createElement('div');
            rankEl.className = `history-card-rank ${rank <= 3 ? 'rank-' + rank : 'rank-other'}`;
            rankEl.textContent = rank;

            const body = document.createElement('div');
            body.className = 'history-card-body';

            const titleEl = document.createElement('div');
            titleEl.className = 'history-card-title';
            const linkEl = document.createElement('a');
            linkEl.href = item.link || '#';
            linkEl.target = '_blank';
            linkEl.rel = 'noopener noreferrer';
            linkEl.textContent = item.title || '无标题';
            titleEl.appendChild(linkEl);

            const meta = document.createElement('div');
            meta.className = 'history-card-meta';

            const sourceBadge = document.createElement('span');
            sourceBadge.className = 'source-badge';
            sourceBadge.textContent = item.source || '未知';
            meta.appendChild(sourceBadge);

            const timeEl = document.createElement('span');
            timeEl.className = 'card-time';
            timeEl.textContent = formatRelativeTime(item.published);
            meta.appendChild(timeEl);

            const hotness = item.hotness || 0;
            let hotnessClass = 'hotness-low';
            if (hotness >= 20) hotnessClass = 'hotness-high';
            else if (hotness >= 12) hotnessClass = 'hotness-medium';
            const hotnessEl = document.createElement('span');
            hotnessEl.className = `hotness-badge ${hotnessClass}`;
            hotnessEl.innerHTML = `🔥 ${hotness}`;
            meta.appendChild(hotnessEl);

            body.appendChild(titleEl);
            body.appendChild(meta);

            if (item.summary) {
                const summaryEl = document.createElement('div');
                summaryEl.className = 'history-card-summary';
                summaryEl.textContent = item.summary;
                body.appendChild(summaryEl);
            }

            if (item.matched_keywords && item.matched_keywords.length > 0) {
                const tagsEl = document.createElement('div');
                tagsEl.className = 'history-card-tags';
                item.matched_keywords.forEach((kw) => {
                    const tag = document.createElement('span');
                    tag.className = 'keyword-tag';
                    tag.textContent = kw;
                    tagsEl.appendChild(tag);
                });
                body.appendChild(tagsEl);
            }

            card.appendChild(rankEl);
            card.appendChild(body);
            list.appendChild(card);
        });

        els.historyContent.innerHTML = '';
        els.historyContent.appendChild(header);
        els.historyContent.appendChild(list);
    }

    // ============================================================
    // v4.1 新增功能
    // ============================================================

    // ---------- 每日一词 ----------
    function initDailyWord() {
        if (!els.dailyWordSection || state.glossaryData.length === 0) return;
        refreshDailyWord();
    }

    function refreshDailyWord() {
        if (state.glossaryData.length === 0) return;
        // 避免短期重复：最近5个不重复
        const recentCount = Math.min(5, state.glossaryData.length - 1);
        let candidates = state.glossaryData.filter(
            (g) => !state.dailyWordHistory.slice(-recentCount).includes(g.term)
        );
        if (candidates.length === 0) candidates = state.glossaryData;
        const term = candidates[Math.floor(Math.random() * candidates.length)];
        state.dailyWordHistory.push(term.term);
        if (state.dailyWordHistory.length > 20) state.dailyWordHistory.shift();

        if (els.dailyWordTerm) els.dailyWordTerm.textContent = term.term;
        if (els.dailyWordDefinition) els.dailyWordDefinition.textContent = term.definition;
        if (els.dailyWordCategory) els.dailyWordCategory.textContent = term.category || '';
    }

    // ---------- 学习路径 ----------
    function openLearningModal() {
        if (!els.learningModal) return;
        openModal(els.learningModal);
        if (state.learningData.length === 0) {
            loadLearningPath();
        } else {
            renderLearningPath();
        }
    }

    async function loadLearningPath() {
        if (!els.learningList) return;
        els.learningList.innerHTML = '<div class="loading-text">加载中...</div>';
        try {
            const res = await fetch('data/learning_path.json');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            state.learningData = await res.json();
            renderLearningPath();
        } catch (err) {
            console.error('学习路径加载失败:', err);
            els.learningList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📚</div><p class="empty-state-text">学习路径加载失败</p><button class="btn-primary" onclick="location.reload()">重试</button></div>';
        }
    }

    function renderLearningPath() {
        if (!els.learningList) return;
        if (!Array.isArray(state.learningData) || state.learningData.length === 0) {
            els.learningList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p class="empty-state-text">暂无学习路径数据</p></div>';
            return;
        }
        const frag = document.createDocumentFragment();
        state.learningData.forEach((cat, idx) => {
            const catEl = document.createElement('div');
            catEl.className = 'learning-category' + (idx === 0 ? ' expanded' : '');
            catEl.innerHTML = `
                <div class="learning-category-header">
                    <span class="learning-category-title">${escapeHtml(cat.title || '未分类')}</span>
                    <span class="learning-category-toggle">▼</span>
                </div>
                <div class="learning-category-items">
                    ${(cat.items || []).map((item) => `<span class="learning-item">${escapeHtml(item)}</span>`).join('')}
                </div>
            `;
            const header = catEl.querySelector('.learning-category-header');
            if (header) {
                header.addEventListener('click', () => {
                    catEl.classList.toggle('expanded');
                });
            }
            frag.appendChild(catEl);
        });
        els.learningList.innerHTML = '';
        els.learningList.appendChild(frag);
    }

    // ---------- 事件时间线 ----------
    function openTimelineModal() {
        if (!els.timelineModal) return;
        openModal(els.timelineModal);
        // 填充关键词下拉框
        populateTimelineKeywords();
    }

    function populateTimelineKeywords() {
        if (!els.timelineKeyword) return;
        // 从 latestData 的 keywords 中获取关键词
        const keywords = [];
        if (state.latestData && state.latestData.keywords) {
            state.latestData.keywords.forEach((k) => {
                if (k && k.keyword) keywords.push(k.keyword);
            });
        }
        // 从 historyData 中补充关键词
        if (Array.isArray(state.historyData)) {
            state.historyData.forEach((h) => {
                if (h.keywords) {
                    h.keywords.forEach((kw) => {
                        if (!keywords.includes(kw)) keywords.push(kw);
                    });
                }
            });
        }
        if (keywords.length === 0) {
            els.timelineKeyword.innerHTML = '<option value="">暂无关键词</option>';
            return;
        }
        els.timelineKeyword.innerHTML = keywords
            .map((k) => `<option value="${escapeHtml(k)}">${escapeHtml(k)}</option>`)
            .join('');
    }

    function loadTimelineData() {
        if (!els.timelineKeyword || !els.timelineInfo) return;
        const keyword = els.timelineKeyword.value;
        if (!keyword) {
            showToast('请先选择关键词');
            return;
        }
        state.currentTimelineKeyword = keyword;

        // 从 historyData 中提取该关键词的每日出现次数
        const timelineData = [];
        if (Array.isArray(state.historyData)) {
            state.historyData.forEach((h) => {
                if (h.date && h.keyword_counts) {
                    const count = h.keyword_counts[keyword] || 0;
                    if (count > 0) {
                        timelineData.push({ date: h.date, count: count });
                    }
                } else if (h.date && h.keywords && h.keywords.includes(keyword)) {
                    // 兼容旧数据：只有关键词列表没有计数
                    timelineData.push({ date: h.date, count: 1 });
                }
            });
        }

        // 按日期排序
        timelineData.sort((a, b) => a.date.localeCompare(b.date));

        if (timelineData.length === 0) {
            els.timelineInfo.innerHTML = '<div class="timeline-hint">该关键词暂无历史数据</div>';
            if (state.timelineChart) {
                state.timelineChart.destroy();
                state.timelineChart = null;
            }
            return;
        }

        renderTimelineChart(timelineData, keyword);
    }

    function renderTimelineChart(data, keyword) {
        if (!els.timelineChart) return;
        const ctx = els.timelineChart.getContext('2d');
        if (state.timelineChart) {
            state.timelineChart.destroy();
        }

        const labels = data.map((d) => d.date);
        const counts = data.map((d) => d.count);

        // 检测热度突增节点（比前一天增长超过50%且绝对值>=2）
        const spikePoints = [];
        for (let i = 1; i < data.length; i++) {
            const prev = data[i - 1].count;
            const curr = data[i].count;
            if (prev > 0 && curr >= prev * 1.5 && curr >= 2) {
                spikePoints.push(data[i].date);
            }
        }

        const pointBgColors = labels.map((d) =>
            spikePoints.includes(d) ? '#F59E0B' : 'rgba(16, 185, 129, 1)'
        );
        const pointRadii = labels.map((d) => (spikePoints.includes(d) ? 7 : 4));

        state.timelineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: keyword + ' 出现次数',
                    data: counts,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: pointBgColors,
                    pointRadius: pointRadii,
                    pointHoverRadius: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        callbacks: {
                            afterLabel: (ctx) => {
                                if (spikePoints.includes(ctx.label)) {
                                    return '🔥 热度突增';
                                }
                                return '';
                            },
                        },
                    },
                },
                scales: {
                    x: { ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } },
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                },
            },
        });

        // 显示统计信息
        const maxCount = Math.max(...counts);
        const maxDate = data[counts.indexOf(maxCount)].date;
        const totalAppear = counts.reduce((a, b) => a + b, 0);
        const spikeHtml = spikePoints.length > 0
            ? `<div class="timeline-stat"><span class="timeline-stat-label">热度突增</span><span class="timeline-stat-value">${spikePoints.length} 次</span></div>`
            : '';

        if (els.timelineInfo) {
            els.timelineInfo.innerHTML = `
                <div class="timeline-stats">
                    <div class="timeline-stat"><span class="timeline-stat-label">首次出现</span><span class="timeline-stat-value">${data[0].date}</span></div>
                    <div class="timeline-stat"><span class="timeline-stat-label">最近出现</span><span class="timeline-stat-value">${data[data.length - 1].date}</span></div>
                    <div class="timeline-stat"><span class="timeline-stat-label">最高热度</span><span class="timeline-stat-value">${maxCount} 次 (${maxDate})</span></div>
                    <div class="timeline-stat"><span class="timeline-stat-label">累计出现</span><span class="timeline-stat-value">${totalAppear} 次</span></div>
                    ${spikeHtml}
                </div>
            `;
        }
    }

    // ---------- 搜索高亮工具 ----------
    function highlightText(text, keyword) {
        if (!text || !keyword) return escapeHtml(text || '');
        const safeText = escapeHtml(text);
        const safeKeyword = escapeHtml(keyword).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp('(' + safeKeyword + ')', 'gi');
        return safeText.replace(regex, '<span class="highlight">$1</span>');
    }

    // ---------- 空状态工具 ----------
    function showEmptyState(container, icon, text, hint, linkText, linkUrl) {
        if (!container) return;
        const linkHtml = linkText && linkUrl
            ? `<a href="${escapeHtml(linkUrl)}" target="_blank" class="empty-state-link">${escapeHtml(linkText)}</a>`
            : '';
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">${icon || '📭'}</div>
                <p class="empty-state-text">${escapeHtml(text || '暂无数据')}</p>
                ${hint ? `<p class="empty-state-hint">${escapeHtml(hint)}</p>` : ''}
                ${linkHtml}
            </div>
        `;
    }

    // ============================================================
    // 启动
    // ============================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
