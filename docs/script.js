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
        // v5.0 新增
        followedKeywords: [],
        sourceHealthData: null,
        keywordDetailChart: null,
        currentDetailKeyword: null,
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
        bindSchoolsEvents();
        bindWindowEvents();
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
        // v5.0 新增
        els.backToTop = document.getElementById('backToTop');
        els.shareSiteBtn = document.getElementById('shareSiteBtn');
        els.sourceHealthBtn = document.getElementById('sourceHealthBtn');
        els.sourceHealthModal = document.getElementById('sourceHealthModal');
        els.sourceHealthOverlay = document.getElementById('sourceHealthOverlay');
        els.sourceHealthClose = document.getElementById('sourceHealthClose');
        els.sourceHealthSummary = document.getElementById('sourceHealthSummary');
        els.sourceHealthList = document.getElementById('sourceHealthList');
        els.keywordDetailModal = document.getElementById('keywordDetailModal');
        els.keywordDetailOverlay = document.getElementById('keywordDetailOverlay');
        els.keywordDetailClose = document.getElementById('keywordDetailClose');
        els.keywordDetailTitle = document.getElementById('keywordDetailTitle');
        els.keywordDetailGlossary = document.getElementById('keywordDetailGlossary');
        els.keywordDetailHotspots = document.getElementById('keywordDetailHotspots');
        els.keywordDetailChart = document.getElementById('keywordDetailChart');
        els.followKeywordBtn = document.getElementById('followKeywordBtn');
        els.featuredSection = document.getElementById('featuredSection');
        els.featuredList = document.getElementById('featuredList');
        els.textColorPicker = document.getElementById('textColorPicker');
        els.fontFamilySelect = document.getElementById('fontFamilySelect');
        els.mobileBottomNav = document.getElementById('mobileBottomNav');
        // v6.0 热度明细
        els.scoreBreakdownModal = document.getElementById('scoreBreakdownModal');
        els.scoreBreakdownTitle = document.getElementById('scoreBreakdownTitle');
        els.scoreBreakdownList = document.getElementById('scoreBreakdownList');
        els.scoreBreakdownTotal = document.getElementById('scoreBreakdownTotal');
        // v6.0 近7天总结
        els.weeklySummarySection = document.getElementById('weeklySummarySection');
        els.weeklySummaryText = document.getElementById('weeklySummaryText');
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
        // 通用模态框关闭：所有带 data-close-modal 属性的元素（关闭按钮、遮罩层）
        document.querySelectorAll('[data-close-modal]').forEach((el) => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                const modal = el.closest('.modal');
                if (modal) {
                    closeModal(modal);
                }
            });
        });

        // ESC 键关闭所有模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAllModals();
                closeCustomizePanel();
            }
        });

        // 搜索
        on(els.searchInput, 'input', handleSearch);

        // 刷新数据
        on(document.getElementById('refreshDataBtn'), 'click', () => {
            showToast('正在刷新数据...');
            loadData();
        });
        // 顶部图标：收藏（设计稿心形）
        on(document.getElementById('savedIcon'), 'click', () => {
            if (typeof openSavedModal === 'function') openSavedModal();
        });
        // 顶部图标：刷新（设计稿刷新）
        on(document.getElementById('reloadIcon'), 'click', () => {
            showToast('正在刷新数据...');
            loadData();
        });
        // 顶部图标：用户反馈（设计稿评论，跳转 GitHub Issues）
        on(document.getElementById('feedbackIcon'), 'click', () => {
            window.open('https://github.com/black15647/hotspot-radar/issues/new?title=网站反馈&body=请描述你的建议或问题：', '_blank', 'noopener');
        });

        // 关注关键词管理（滚动到标签云）
        on(document.getElementById('followedManageBtn'), 'click', () => {
            const cloud = document.getElementById('tagCloud');
            if (cloud) {
                cloud.scrollIntoView({ behavior: 'smooth', block: 'center' });
                showToast('点击下方关键词可查看详情或取消关注');
            }
        });

        // 页脚 data-open-modal 快捷入口
        document.querySelectorAll('[data-open-modal]').forEach((el) => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const sel = el.getAttribute('data-open-modal');
                const m = document.querySelector(sel);
                if (m && typeof openModal === 'function') openModal(m);
            });
        });

        // 暗黑模式
        on(els.themeToggle, 'click', toggleDarkMode);

        // 主题定制面板
        on(els.customizeBtn, 'click', openCustomizePanel);
        on(els.panelClose, 'click', closeCustomizePanel);
        on(els.panelOverlay, 'click', closeCustomizePanel);

        on(els.primaryColorPicker, 'input', (e) => {
            setCSSVar('--clr-brand', e.target.value);
            saveTheme();
        });
        on(els.bgColorPicker, 'input', (e) => {
            setCSSVar('--clr-bg', e.target.value);
            saveTheme();
        });
        on(els.radiusSlider, 'input', (e) => {
            const val = e.target.value;
            if (els.radiusValue) els.radiusValue.textContent = val;
            setCSSVar('--r-md', val + 'px');
            saveTheme();
        });
        on(els.fontSizeSlider, 'input', (e) => {
            const val = e.target.value;
            if (els.fontSizeValue) els.fontSizeValue.textContent = val;
            setCSSVar('--fz-base', val + 'px');
            saveTheme();
        });

        // 密度单选
        document.querySelectorAll('input[name="density"]').forEach((radio) => {
            radio.addEventListener('change', (e) => {
                setCSSVar('--sp-card', e.target.value + 'px');
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

        // v5.0 新增事件
        // 回到顶部
        on(els.backToTop, 'click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
        // 页脚"回到顶部"链接（与悬浮按钮功能相同，避免重复 ID）
        on(document.getElementById('footerBackToTop'), 'click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
        window.addEventListener('scroll', handleScroll);
        // 分享网站
        on(els.shareSiteBtn, 'click', shareSite);
        // 源健康度
        on(els.sourceHealthBtn, 'click', openSourceHealthModal);
        on(els.sourceHealthOverlay, 'click', () => closeModal(els.sourceHealthModal));
        on(els.sourceHealthClose, 'click', () => closeModal(els.sourceHealthModal));
        // 关键词详情
        on(els.keywordDetailOverlay, 'click', () => closeModal(els.keywordDetailModal));
        on(els.keywordDetailClose, 'click', () => closeModal(els.keywordDetailModal));
        on(els.followKeywordBtn, 'click', toggleFollowKeyword);
        // 主题定制新增
        on(els.textColorPicker, 'input', () => { saveTheme(); applyTheme(getCurrentTheme()); });
        on(els.fontFamilySelect, 'change', () => { saveTheme(); applyTheme(getCurrentTheme()); });
        // 移动端底部导航
        if (els.mobileBottomNav) {
            els.mobileBottomNav.querySelectorAll('.mobile-nav-item').forEach((btn) => {
                btn.addEventListener('click', () => handleMobileNav(btn.dataset.target));
            });
        }

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
            // v5.0 新功能
            loadFollowedKeywords();
            renderFeatured();
            renderFollowedKeywordsBar();
            // v6.0 近7天热度总结
            loadWeeklySummary(state.latestData);
            // 页面元信息（日期 / 趋势关键词 / 统计卡）
            renderPageMeta();
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
        hotnessEl.className = `hotness-badge hotness-score ${hotnessClass}`;
        hotnessEl.innerHTML = `🔥 ${hotness}`;
        hotnessEl.title = '点击查看热度明细';
        hotnessEl.addEventListener('click', (e) => {
            e.stopPropagation();
            openScoreBreakdown(item);
        });
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
                        openKeywordDetail(kw);
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

            tag.addEventListener('click', () => openKeywordDetail(kw.keyword));
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

        // 从 latest.json 中读取 weekly_keywords（前3个高频词）
        const weeklyKeywords = (state.latestData && state.latestData.weekly_keywords) || [];
        const topKeywords = weeklyKeywords.slice(0, 3).map(kw => kw.term || kw.keyword);

        if (state.trendChart) {
            state.trendChart.destroy();
        }

        const isDark = document.body.classList.contains('dark');
        const textColor = isDark ? '#94A3B8' : '#6B7280';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(107, 114, 128, 0.1)';

        // 如果没有高频词数据，显示资讯条数
        let datasets = [];
        const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6'];

        if (topKeywords.length > 0) {
            // 为每个高频词统计近7天出现次数
            topKeywords.forEach((keyword, idx) => {
                const color = colors[idx % colors.length];
                const data = recent7.map((day) => {
                    const dayKeywords = day.keywords || [];
                    let count = 0;
                    dayKeywords.forEach(kw => {
                        const term = kw.term || kw.keyword || kw;
                        if (term === keyword) {
                            count = kw.count || 1;
                        }
                    });
                    return count;
                });
                datasets.push({
                    label: keyword,
                    data: data,
                    borderColor: color,
                    backgroundColor: color + '20',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointBackgroundColor: color,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                });
            });
        } else {
            // 没有高频词，显示资讯条数
            const data = recent7.map((h) => h.total_items || 0);
            datasets.push({
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
            });
        }

        state.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: topKeywords.length > 0,
                        position: 'top',
                        labels: {
                            color: textColor,
                            font: { size: 12 },
                            usePointStyle: true,
                            padding: 15,
                        },
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

    function copyToClipboard(text, message) {
        const msg = message || '链接已复制！';
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showToast(msg);
            }).catch(() => {
                fallbackCopy(text, msg);
            });
        } else {
            fallbackCopy(text, msg);
        }
    }

    function fallbackCopy(text, message) {
        const msg = message || '链接已复制！';
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showToast(msg);
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
            setCSSVar('--clr-brand', theme.primaryColor);
            els.primaryColorPicker.value = theme.primaryColor;
        }
        if (theme.bgColor) {
            setCSSVar('--clr-bg', theme.bgColor);
            els.bgColorPicker.value = theme.bgColor;
        }
        if (theme.borderRadius !== undefined) {
            setCSSVar('--r-md', theme.borderRadius + 'px');
            els.radiusSlider.value = theme.borderRadius;
            els.radiusValue.textContent = theme.borderRadius;
        }
        if (theme.cardPadding !== undefined) {
            setCSSVar('--sp-card', theme.cardPadding + 'px');
            document.querySelectorAll('input[name="density"]').forEach((radio) => {
                radio.checked = parseInt(radio.value) === theme.cardPadding;
            });
        }
        if (theme.fontSize !== undefined) {
            setCSSVar('--fz-base', theme.fontSize + 'px');
            els.fontSizeSlider.value = theme.fontSize;
            els.fontSizeValue.textContent = theme.fontSize;
        }
        if (theme.textColor) {
            setCSSVar('--clr-text', theme.textColor);
            if (els.textColorPicker) els.textColorPicker.value = theme.textColor;
        }
        if (theme.fontFamily) {
            const fontMap = {
                'system': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                'sans-serif': 'Arial, Helvetica, sans-serif',
                'serif': 'Georgia, "Times New Roman", serif',
                'monospace': '"Courier New", Courier, monospace',
            };
            document.body.style.fontFamily = fontMap[theme.fontFamily] || fontMap['system'];
            if (els.fontFamilySelect) els.fontFamilySelect.value = theme.fontFamily;
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
            textColor: els.textColorPicker ? els.textColorPicker.value : '#111827',
            fontFamily: els.fontFamilySelect ? els.fontFamilySelect.value : 'system',
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
        if (els.dailyWordDefinition) {
            els.dailyWordDefinition.textContent = term.definition;
            // 重置展开状态
            els.dailyWordDefinition.classList.remove('expanded');
            // 绑定点击展开/收起事件（只绑定一次）
            if (!els.dailyWordDefinition.dataset.bound) {
                els.dailyWordDefinition.dataset.bound = 'true';
                els.dailyWordDefinition.addEventListener('click', () => {
                    els.dailyWordDefinition.classList.toggle('expanded');
                });
            }
        }
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
    // v5.0 新增功能
    // ============================================================

    // ---------- 回到顶部 ----------
    function handleScroll() {
        if (els.backToTop) {
            if (window.scrollY > 300) {
                els.backToTop.classList.add('visible');
            } else {
                els.backToTop.classList.remove('visible');
            }
        }
    }

    // ---------- 分享网站 ----------
    function shareSite() {
        const shareData = {
            title: '环境学子雷达',
            text: '面向环境专业学生的免费开源热点聚合与学习平台',
            url: window.location.href,
        };
        if (navigator.share) {
            navigator.share(shareData).catch(() => {});
        } else {
            copyToClipboard(window.location.href, '网站链接已复制，快去分享吧！');
        }
    }

    // ---------- 源健康度 ----------
    function openSourceHealthModal() {
        if (!els.sourceHealthModal) return;
        openModal(els.sourceHealthModal);
        loadSourceHealth();
    }

    async function loadSourceHealth() {
        if (!els.sourceHealthList) return;
        els.sourceHealthList.innerHTML = '<div class="loading-text">加载中...</div>';
        try {
            const res = await fetch('data/source_health.json');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            state.sourceHealthData = await res.json();
            renderSourceHealth();
        } catch (err) {
            console.error('源健康度加载失败:', err);
            els.sourceHealthList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📡</div><p class="empty-state-text">暂无源健康度数据</p></div>';
        }
    }

    function renderSourceHealth() {
        if (!els.sourceHealthList || !state.sourceHealthData) return;
        const data = state.sourceHealthData;
        // 渲染摘要
        if (els.sourceHealthSummary) {
            els.sourceHealthSummary.innerHTML = `
                <div class="source-health-stat">
                    <div class="source-health-stat-value">${data.total_sources || 0}</div>
                    <div class="source-health-stat-label">总源数</div>
                </div>
                <div class="source-health-stat">
                    <div class="source-health-stat-value success">${data.success_count || 0}</div>
                    <div class="source-health-stat-label">成功</div>
                </div>
                <div class="source-health-stat">
                    <div class="source-health-stat-value failed">${data.failed_count || 0}</div>
                    <div class="source-health-stat-label">失败</div>
                </div>
                <div class="source-health-stat">
                    <div class="source-health-stat-value critical">${data.critical_count || 0}</div>
                    <div class="source-health-stat-label">严重</div>
                </div>
            `;
        }
        // 渲染列表
        const sources = data.sources || [];
        const frag = document.createDocumentFragment();
        sources.forEach((src) => {
            const item = document.createElement('div');
            const statusClass = src.critical ? 'critical' : (src.success ? '' : 'failed');
            item.className = 'source-health-item ' + statusClass;
            const statusIcon = src.success ? '✅' : '❌';
            const criticalBadge = src.critical ? '<span class="source-health-badge critical">连续失败</span>' : '';
            item.innerHTML = `
                <span class="source-health-status">${statusIcon}</span>
                <div class="source-health-info">
                    <div class="source-health-name">${escapeHtml(src.name || '未知源')}</div>
                    <div class="source-health-meta">${src.elapsed_seconds || 0}s · ${src.item_count || 0} 条 · ${src.last_check ? new Date(src.last_check).toLocaleString('zh-CN') : '未知'}</div>
                    ${src.error ? `<div class="source-health-error">${escapeHtml(src.error)}</div>` : ''}
                </div>
                ${criticalBadge}
            `;
            frag.appendChild(item);
        });
        els.sourceHealthList.innerHTML = '';
        els.sourceHealthList.appendChild(frag);
    }

    // ---------- 关键词详情 ----------
    function openKeywordDetail(keyword) {
        if (!els.keywordDetailModal) return;
        state.currentDetailKeyword = keyword;
        if (els.keywordDetailTitle) els.keywordDetailTitle.textContent = '🔍 ' + keyword;
        // 更新关注按钮状态
        updateFollowButtonState();
        openModal(els.keywordDetailModal);
        renderKeywordDetail(keyword);
    }

    function renderKeywordDetail(keyword) {
        // 知识库解释
        if (els.keywordDetailGlossary) {
            const term = state.glossaryMap[keyword];
            if (term) {
                els.keywordDetailGlossary.innerHTML = `
                    <span class="glossary-category">${escapeHtml(term.category || '')}</span>
                    <div class="glossary-def">${escapeHtml(term.definition || '')}</div>
                `;
            } else {
                els.keywordDetailGlossary.innerHTML = `
                    <p class="text-muted">暂无解释，可<a href="https://github.com/你的用户名/你的仓库名/issues/new?title=建议收录词条：${encodeURIComponent(keyword)}&body=请解释这个环境专业术语：" target="_blank" class="empty-state-link">提交收录</a></p>
                `;
            }
        }
        // 今日相关热点
        if (els.keywordDetailHotspots && state.latestData) {
            const related = (state.latestData.items || []).filter((item) => {
                const text = (item.title || '') + (item.summary || '');
                return text.toLowerCase().includes(keyword.toLowerCase());
            }).slice(0, 5);
            if (related.length === 0) {
                els.keywordDetailHotspots.innerHTML = '<p class="text-muted">今日暂无相关热点</p>';
            } else {
                const frag = document.createDocumentFragment();
                related.forEach((item) => {
                    const div = document.createElement('div');
                    div.className = 'keyword-detail-hotspot-item';
                    div.innerHTML = `
                        <div class="keyword-detail-hotspot-title">${escapeHtml(item.title || '')}</div>
                        <div class="keyword-detail-hotspot-meta">
                            <span>${escapeHtml(item.source || '')}</span>
                            <span>热度 ${Math.round(item.score || 0)}</span>
                        </div>
                    `;
                    frag.appendChild(div);
                });
                els.keywordDetailHotspots.innerHTML = '';
                els.keywordDetailHotspots.appendChild(frag);
            }
        }
        // 365天趋势图
        renderKeywordDetailChart(keyword);
    }

    function renderKeywordDetailChart(keyword) {
        if (!els.keywordDetailChart) return;
        const ctx = els.keywordDetailChart.getContext('2d');
        if (state.keywordDetailChart) state.keywordDetailChart.destroy();
        // 从 historyData 提取数据
        const data = [];
        if (Array.isArray(state.historyData)) {
            state.historyData.forEach((h) => {
                if (h.date && h.keyword_counts) {
                    const count = h.keyword_counts[keyword] || 0;
                    if (count > 0) data.push({ date: h.date, count: count });
                }
            });
        }
        data.sort((a, b) => a.date.localeCompare(b.date));
        const labels = data.map((d) => d.date);
        const counts = data.map((d) => d.count);
        state.keywordDetailChart = new Chart(ctx, {
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
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, position: 'top' } },
                scales: {
                    x: { ticks: { maxRotation: 45, minRotation: 45, font: { size: 10 } } },
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                },
            },
        });
    }

    // ---------- 关注关键词 ----------
    function loadFollowedKeywords() {
        try {
            const saved = localStorage.getItem('followed_keywords');
            state.followedKeywords = saved ? JSON.parse(saved) : [];
        } catch (e) {
            state.followedKeywords = [];
        }
    }

    function saveFollowedKeywords() {
        try {
            localStorage.setItem('followed_keywords', JSON.stringify(state.followedKeywords));
        } catch (e) {}
    }

    function toggleFollowKeyword() {
        const kw = state.currentDetailKeyword;
        if (!kw) return;
        const idx = state.followedKeywords.indexOf(kw);
        if (idx >= 0) {
            state.followedKeywords.splice(idx, 1);
            showToast('已取消关注：' + kw);
        } else {
            state.followedKeywords.push(kw);
            showToast('已关注：' + kw);
        }
        saveFollowedKeywords();
        updateFollowButtonState();
        renderFollowedKeywordsBar();
    }

    function updateFollowButtonState() {
        if (!els.followKeywordBtn) return;
        const kw = state.currentDetailKeyword;
        const followed = state.followedKeywords.includes(kw);
        els.followKeywordBtn.textContent = followed ? '⭐ 已关注（点击取消）' : '⭐ 关注这个词';
        els.followKeywordBtn.classList.toggle('followed', followed);
    }

    function renderFollowedKeywordsBar() {
        // 在今日热点区域顶部显示已关注关键词标签
        if (!els.cardList || state.followedKeywords.length === 0) return;
        // 检查是否已存在
        let bar = document.getElementById('followedKeywordsBar');
        if (!bar) {
            bar = document.createElement('div');
            bar.id = 'followedKeywordsBar';
            bar.className = 'followed-keywords-bar';
            els.cardList.parentNode.insertBefore(bar, els.cardList);
        }
        bar.innerHTML = '<span class="followed-keywords-label">⭐ 已关注：</span>' +
            state.followedKeywords.map((kw) =>
                `<span class="followed-keyword-tag" data-kw="${escapeHtml(kw)}">${escapeHtml(kw)} <span class="remove">×</span></span>`
            ).join('');
        // 显示外层区块
        const followedBlock = document.getElementById('followedBlock');
        if (followedBlock) followedBlock.style.display = 'block';
        // 绑定点击事件
        bar.querySelectorAll('.followed-keyword-tag').forEach((tag) => {
            tag.addEventListener('click', () => {
                const kw = tag.dataset.kw;
                if (els.searchInput) {
                    els.searchInput.value = kw;
                    els.searchInput.dispatchEvent(new Event('input'));
                }
            });
        });
    }

    // ---------- 今日焦点 ----------
    function renderFeatured() {
        if (!els.featuredSection || !els.featuredList || !state.latestData) return;
        const items = state.latestData.items || [];
        if (items.length === 0) {
            els.featuredSection.style.display = 'none';
            return;
        }
        // 取热度前2条
        const top2 = items.slice(0, 2);
        const frag = document.createDocumentFragment();
        top2.forEach((item, idx) => {
            const card = document.createElement('div');
            card.className = 'featured-card';
            card.innerHTML = `
                <div class="featured-title">${escapeHtml(item.title || '')}</div>
                <div class="featured-source">${escapeHtml(item.source || '')}</div>
                <div class="featured-analysis">${escapeHtml(item.analysis || '该条目涉及环境领域话题，建议关注。')}</div>
            `;
            card.addEventListener('click', () => {
                // 滚动到对应卡片并展开
                const cards = els.cardList.querySelectorAll('.card');
                if (cards[idx]) {
                    cards[idx].scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
            frag.appendChild(card);
        });
        els.featuredList.innerHTML = '';
        els.featuredList.appendChild(frag);
        els.featuredSection.style.display = 'block';
    }

    // ---------- 移动端底部导航 ----------
    function handleMobileNav(target) {
        // 更新激活状态
        if (els.mobileBottomNav) {
            els.mobileBottomNav.querySelectorAll('.mobile-nav-item').forEach((btn) => {
                btn.classList.toggle('is-active', btn.dataset.target === target);
            });
        }
        switch (target) {
            case 'hotspot':
                switchWindow('hotspot');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                break;
            case 'schools':
                switchWindow('schools');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                break;
            case 'jobs':
                switchWindow('jobs');
                window.scrollTo({ top: 0, behavior: 'smooth' });
                break;
            case 'glossary':
                if (els.glossaryBtn) els.glossaryBtn.click();
                break;
            case 'history':
                if (els.historyBtn) els.historyBtn.click();
                break;
            case 'saved':
                if (els.savedBtn) els.savedBtn.click();
                break;
        }
    }

    // ---------- 获取当前主题 ----------
    function getCurrentTheme() {
        return {
            primaryColor: els.primaryColorPicker.value,
            bgColor: els.bgColorPicker.value,
            textColor: els.textColorPicker ? els.textColorPicker.value : '#111827',
            fontFamily: els.fontFamilySelect ? els.fontFamilySelect.value : 'system',
            borderRadius: parseInt(els.radiusSlider.value),
            cardPadding: parseInt(document.querySelector('input[name="density"]:checked').value),
            fontSize: parseInt(els.fontSizeSlider.value),
            dark: document.body.classList.contains('dark'),
        };
    }

    // ---------- 为什么是热点 ----------
    function generateWhyHot(item) {
        const reasons = [];
        const score = item.score || item.hotness || 0;
        const source = item.source || '';
        const keywords = item.matched_keywords || item.keywords || [];
        const published = item.published || '';
        // 来源权重
        if (source.includes('Nature') || source.includes('Water Research')) {
            reasons.push('来源权威性高（' + source + '）');
        } else if (source.includes('Google News')) {
            reasons.push('来源为聚合新闻（' + source + '）');
        }
        // 关键词匹配
        if (keywords.length > 0) {
            reasons.push('匹配 ' + keywords.length + ' 个环境专业关键词（' + keywords.slice(0, 3).join('、') + '）');
        }
        // 时间新鲜度
        if (published) {
            try {
                const pubDate = new Date(published);
                const hoursAgo = (Date.now() - pubDate.getTime()) / 3600000;
                if (hoursAgo < 24) {
                    reasons.push('发布时间新鲜（约' + Math.round(hoursAgo) + '小时前）');
                }
            } catch (e) {}
        }
        // 热度分数
        let level = '中等热度';
        if (score >= 20) level = '高热度';
        else if (score < 12) level = '一般热度';
        const kw = keywords.length > 0 ? '#' + keywords[0] + ' ' : '';
        return kw + '近24小时' + level + '（' + Math.round(score) + '分），主要因为：' +
            (reasons.length > 0 ? reasons.map((r, i) => (i + 1) + '. ' + r).join('；') : '综合因素驱动') + '。';
    }

    // ---------- 重写关键词标签点击行为（打开详情而非趋势图） ----------
    // 在 renderCards 中绑定的关键词标签点击事件会调用 openKeywordDetail
    // 这里保留原有的 openKeywordChart 函数，但关键词标签默认打开详情

    // ---------- 初始化 v5.0 功能 ----------
    function initV5() {
        loadFollowedKeywords();
        // 在数据加载完成后渲染今日焦点和关注关键词
        const origRenderAll = renderAll;
        // 重写 renderAll 以包含新功能
        window._renderAllV5 = function() {
            origRenderAll();
            renderFeatured();
            renderFollowedKeywordsBar();
        };
    }

    // 在 init 中调用 initV5
    const _origInit = init;
    // 注意：init 已经定义，我们通过在 loadData 完成后调用新功能来实现

    // ============================================================
    // v6.0 热度分数明细
    // ============================================================
    function openScoreBreakdown(item) {
        if (!els.scoreBreakdownModal) return;
        const title = item.title || '未知标题';
        const breakdown = item.score_breakdown || null;

        if (els.scoreBreakdownTitle) {
            els.scoreBreakdownTitle.textContent = title.length > 40 ? title.substring(0, 40) + '...' : title;
        }

        const listEl = els.scoreBreakdownList;
        if (listEl) {
            listEl.innerHTML = '';
            if (breakdown && typeof breakdown === 'object') {
                const labels = {
                    base: '基础分',
                    source_score: '来源权重分',
                    keyword_score: '关键词匹配分',
                    time_score: '时间新鲜度分',
                    topic_bonus: '主题聚合加分',
                    total: '总分'
                };
                for (const [key, value] of Object.entries(breakdown)) {
                    if (key === 'total') continue;
                    const itemEl = document.createElement('div');
                    itemEl.className = 'score-breakdown-item';
                    itemEl.innerHTML = `<span class="score-breakdown-item-label">${labels[key] || key}</span><span class="score-breakdown-item-value">+${Number(value).toFixed(1)}</span>`;
                    listEl.appendChild(itemEl);
                }
            } else if (typeof breakdown === 'string') {
                listEl.innerHTML = `<div class="score-breakdown-item"><span class="score-breakdown-item-label">${breakdown}</span></div>`;
            } else {
                listEl.innerHTML = `<div class="score-breakdown-item"><span class="score-breakdown-item-label">暂无明细数据（该条未包含 score_breakdown 字段，由后端热度算法生成）</span></div>`;
            }
        }

        if (els.scoreBreakdownTotal) {
            const total = breakdown && breakdown.total ? breakdown.total : (item.hotness || item.score || 0);
            els.scoreBreakdownTotal.innerHTML = `<span>总分</span><span>${Number(total).toFixed(1)}</span>`;
        }

        openModal(els.scoreBreakdownModal);
    }

    // ============================================================
    // v6.0 近7天热度总结
    // ============================================================
    // ============================================================
    // 页面元信息：日期、本周高频关键词、统计卡
    // ============================================================
    function renderPageMeta() {
        // 1) 页面日期
        const dateEl = document.getElementById('pageDate');
        if (dateEl) {
            const now = new Date();
            const weeks = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
            let srcCount = 0;
            if (state.latestData && state.latestData.items) {
                srcCount = new Set(state.latestData.items.map((it) => it.source).filter(Boolean)).size;
            }
            const srcTxt = srcCount > 0 ? ` · 已抓取 ${srcCount} 个 RSS 源` : ' · 每日聚合 · 数据自动更新';
            dateEl.textContent = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 · ${weeks[now.getDay()]}${srcTxt}`;
        }

        // 2) 本周高频关键词（取关键词分析前4个）
        const trendEl = document.getElementById('trendKeywords');
        if (trendEl) {
            const kw = (state.latestData && state.latestData.keyword_analysis) || [];
            if (kw.length > 0) {
                trendEl.textContent = kw.slice(0, 4).map((k) => k.keyword || k).join(' · ');
            } else if (state.latestData && state.latestData.keywords) {
                trendEl.textContent = state.latestData.keywords.slice(0, 4).join(' · ');
            } else {
                trendEl.textContent = '暂无足够数据';
            }
        }

        // 3) 底部统计卡（近7天）
        const statTotal = document.getElementById('statTotal');
        const statKeywords = document.getElementById('statKeywords');
        const statPolicy = document.getElementById('statPolicy');
        if (!statTotal) return;

        const hist = state.historyData || [];
        if (hist.length > 0) {
            const last7 = hist.slice(-7);
            const totalItems = last7.reduce((acc, d) => acc + (parseInt(d.total_items) || 0), 0);
            const kwSet = new Set();
            last7.forEach((d) => {
                (d.keywords || []).forEach((k) => kwSet.add(k));
            });
            statTotal.textContent = totalItems;
            statKeywords.textContent = kwSet.size;
            // 政策类占比：关键词含政策/督察/法规/环评/法规等
            let policy = 0;
            kwSet.forEach((k) => {
                if (/政策|督察|法规|环评|条例|标准|执法/.test(String(k))) policy++;
            });
            const ratio = kwSet.size > 0 ? Math.round((policy / kwSet.size) * 100) : 0;
            statPolicy.textContent = ratio + '%';
        } else {
            // 无历史数据：用当日关键词分析估算
            const kw = (state.latestData && state.latestData.keyword_analysis) || [];
            statTotal.textContent = (state.latestData && state.latestData.total_items) || 0;
            statKeywords.textContent = kw.length;
            let policy = 0;
            kw.forEach((k) => {
                if (/政策|督察|法规|环评|条例|标准|执法/.test(String(k.keyword || k))) policy++;
            });
            statPolicy.textContent = kw.length > 0 ? Math.round((policy / kw.length) * 100) + '%' : '--';
        }
    }

    function loadWeeklySummary(data) {
        const weeklySummary = data.weekly_summary || data.weeklySummary || '';
        if (!els.weeklySummarySection || !els.weeklySummaryText) return;

        if (weeklySummary && weeklySummary.trim()) {
            els.weeklySummaryText.textContent = weeklySummary;
            els.weeklySummarySection.style.display = 'block';
        } else {
            els.weeklySummarySection.style.display = 'none';
        }
    }

    

    // ============================================================
    // 考研院校分析模块
    // ============================================================

    // 获取难度等级
    function getDifficultyLevel(score) {
        if (score >= 80) return 'high';
        if (score >= 65) return 'medium-high';
        if (score >= 50) return 'medium';
        if (score >= 35) return 'low';
        return 'easy';
    }

    // 获取难度等级文字
    function getDifficultyText(score) {
        if (score >= 80) return '高难度';
        if (score >= 65) return '中高难度';
        if (score >= 50) return '中等难度';
        if (score >= 35) return '低难度';
        return '容易';
    }


    // 绑定考研院校入口（🎓 工具按钮 → 切换到高校考研窗口，统一入口）
    function bindSchoolsEvents() {
        const schoolsBtn = document.getElementById('schoolsBtn');
        if (schoolsBtn) {
            schoolsBtn.addEventListener('click', () => {
                switchWindow('schools');
            });
        }
    }


// ============================================================
    // 启动
    // ============================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }


    // ============================================================
    // 就业方向窗口
    // ============================================================
    let jobsRendered = false;

    // 十大就业方向数据
    const jobDirections = [
        { name: '环境监测与评价', desc: '环评、监测、第三方检测机构核心岗位', jobs: '环评工程师 · 监测员', demand: '需求高', demandLevel: 'high' },
        { name: '水处理与给排水', desc: '市政水务、工业废水处理、膜技术方向', jobs: '工艺工程师 · 运维', demand: '需求高', demandLevel: 'high' },
        { name: '大气治理与气候', desc: '脱硫脱硝、碳减排、气候政策研究', jobs: '大气工程师 · 碳管理', demand: '需求中高', demandLevel: 'medium' },
        { name: '固废与资源循环', desc: '垃圾分类、危废处置、再生资源利用', jobs: '固废工程师 · 资源化', demand: '需求中', demandLevel: 'low' },
        { name: '生态修复与保护', desc: '土壤修复、湿地保护、生物多样性', jobs: '修复工程师 · 生态员', demand: '需求中', demandLevel: 'low' },
        { name: '环境咨询与ESG', desc: 'ESG报告、碳核查、绿色咨询', jobs: 'ESG顾问 · 咨询师', demand: '需求高', demandLevel: 'high' },
        { name: '环保技术研发', desc: '环保装备、新材料、智慧环保算法', jobs: '研发工程师 · 算法', demand: '需求中高', demandLevel: 'medium' },
        { name: '环境与公共卫生', desc: '环境健康、毒理、职业健康', jobs: '公卫研究员 · 毒理', demand: '需求中', demandLevel: 'low' },
        { name: '环境政策与规划', desc: '生态环境规划、政策研究、行政管理', jobs: '规划师 · 公务员', demand: '需求中', demandLevel: 'low' },
        { name: '绿色金融与碳管理', desc: '碳交易、绿色债券、气候投融资', jobs: '碳交易员 · 分析师', demand: '需求高', demandLevel: 'high' }
    ];

    // 招聘资讯示例数据
    const recruitData = [
        { company: '某环境监测中心', salary: '8-12K', job: '环评工程师', meta: '广州 · 1-3年 · 全职急招' },
        { company: '某水务集团', salary: '10-15K', job: '水处理工艺工程师', meta: '深圳 · 3-5年 · 国企' },
        { company: '某碳中和研究院', salary: '12-18K', job: '碳资产管理', meta: '北京 · 经验不限 · 研究岗' },
        { company: '某环保科技公司', salary: '9-14K', job: 'ESG咨询顾问', meta: '上海 · 1-3年 · 成长快' }
    ];

    // 需求程度样式
    function getDemandClass(level) {
        if (level === 'high') return 'demand-high';
        if (level === 'medium') return 'demand-medium';
        return 'demand-low';
    }

    // 渲染就业方向页面
    function renderJobsPage() {
        const grid = document.getElementById('jobsGrid');
        const recruitGrid = document.getElementById('recruitGrid');
        if (!grid || !recruitGrid) return;

        // 渲染十大方向卡片
        grid.innerHTML = jobDirections.map(dir => {
            return '' +
                '<div class="job-card">' +
                    '<h3 class="job-card-title">' + dir.name + '</h3>' +
                    '<p class="job-card-desc">' + dir.desc + '</p>' +
                    '<p class="job-card-roles">岗位：' + dir.jobs + '</p>' +
                    '<span class="job-demand ' + getDemandClass(dir.demandLevel) + '">' + dir.demand + '</span>' +
                '</div>';
        }).join('');

        // 渲染招聘资讯
        recruitGrid.innerHTML = recruitData.map(rec => {
            return '' +
                '<div class="recruit-card">' +
                    '<div class="recruit-card-header">' +
                        '<span class="recruit-company">' + rec.company + '</span>' +
                        '<span class="recruit-salary">' + rec.salary + '</span>' +
                    '</div>' +
                    '<p class="recruit-job">岗位：' + rec.job + '</p>' +
                    '<p class="recruit-meta">' + rec.meta + '</p>' +
                '</div>';
        }).join('');

        jobsRendered = true;
    }

    // ============================================================
    // 双窗口切换逻辑
    // ============================================================
    let currentWindow = 'hotspot';
    let schoolsDataPage = [];
    let filteredSchoolsPage = [];
    let schoolsLoaded = false;

    // 切换窗口
    function switchWindow(windowName) {
        currentWindow = windowName;
        // 更新标签状态
        document.querySelectorAll('.nav-tab').forEach(tab => {
            if (tab.dataset.window === windowName) {
                tab.classList.add('is-active');
            } else {
                tab.classList.remove('is-active');
            }
        });
        // 更新面板显示
        document.querySelectorAll('.window-pane').forEach(pane => {
            pane.classList.remove('is-active');
        });
        if (windowName === 'hotspot') {
            document.getElementById('hotspotWindow').classList.add('is-active');
        } else if (windowName === 'schools') {
            document.getElementById('schoolsWindow').classList.add('is-active');
            // 首次进入高校考研窗口时加载数据
            if (!schoolsLoaded) {
                loadSchoolsDataPage();
            }
        } else if (windowName === 'jobs') {
            document.getElementById('jobsWindow').classList.add('is-active');
            // 首次进入就业方向窗口时渲染数据
            if (!jobsRendered) {
                renderJobsPage();
            }
        }
    }

    // 加载学校数据（页面版）
    async function loadSchoolsDataPage() {
        try {
            const response = await fetch('data/schools.json');
            if (!response.ok) throw new Error('加载失败');
            schoolsDataPage = await response.json();
            filteredSchoolsPage = [...schoolsDataPage];
            schoolsLoaded = true;
            filterSchoolsPage();
            return true;
        } catch (err) {
            console.error('加载院校数据失败:', err);
            document.getElementById('schoolsList2').innerHTML = '<div class="schools-empty">院校数据加载失败，请稍后重试</div>';
            return false;
        }
    }

    // 筛选学校（页面版）
    function filterSchoolsPage() {
        const searchText = document.getElementById('schoolsSearch2');
        if (!searchText) return;
        const searchVal = searchText.value.toLowerCase();
        // 层次多选：收集所有选中的具体层次（不含"全部"）
        const selLevels = [];
        document.querySelectorAll('.school-level-btn.is-active').forEach((b) => {
            const lv = b.dataset.level;
            if (lv && lv !== 'all') selLevels.push(lv);
        });
        // 难度多选：收集所有选中的具体难度（不含"全部"）
        const selDiffs = [];
        document.querySelectorAll('.school-diff-btn.is-active').forEach((b) => {
            const d = b.dataset.diff;
            if (d && d !== 'all') selDiffs.push(d);
        });

        filteredSchoolsPage = schoolsDataPage.filter((school) => {
            // 层次筛选（并集）：命中任一选中层次即通过
            if (selLevels.length > 0) {
                const ok = selLevels.some((lv) => {
                    if (lv === '普通') {
                        return !(school.level.includes('985') || school.level.includes('211') || school.level.includes('双一流'));
                    }
                    return school.level.includes(lv);
                });
                if (!ok) return false;
            }
            // 难度筛选（并集）
            if (selDiffs.length > 0) {
                const lv = getDifficultyLevel(school.difficulty_index);
                if (!selDiffs.includes(lv)) return false;
            }
            // 搜索
            if (searchVal && !school.name.toLowerCase().includes(searchVal)) return false;
            return true;
        });

        sortSchoolsPage();
        renderSchoolsListPage();
    }

    // 排序学校（页面版）：难度升序 / 降序按钮
    function sortSchoolsPage() {
        const ascBtn = document.querySelector('.school-sort-btn[data-sort="asc"]');
        const isAsc = ascBtn && ascBtn.classList.contains('is-active');
        filteredSchoolsPage.sort((a, b) => (isAsc ? a.difficulty_index - b.difficulty_index : b.difficulty_index - a.difficulty_index));
    }

    // 渲染学校列表（页面版）
    function renderSchoolsListPage() {
        const listEl = document.getElementById('schoolsList2');
        const statsEl = document.getElementById('schoolsStats2');
        if (!listEl || !statsEl) return;

        if (filteredSchoolsPage.length === 0) {
            listEl.innerHTML = '<div class="schools-empty">没有符合条件的院校</div>';
            statsEl.textContent = '';
            return;
        }

        const avgDifficulty = (filteredSchoolsPage.reduce((sum, s) => sum + s.difficulty_index, 0) / filteredSchoolsPage.length).toFixed(1);
        const highCount = filteredSchoolsPage.filter(s => s.difficulty_index >= 80).length;
        const easyCount = filteredSchoolsPage.filter(s => s.difficulty_index < 35).length;
        statsEl.innerHTML = '共 <strong>' + filteredSchoolsPage.length + '</strong> 所院校 | 平均难度指数 <strong>' + avgDifficulty + '</strong> | 高难度 <strong>' + highCount + '</strong> 所 | 容易 <strong>' + easyCount + '</strong> 所';

        const html = filteredSchoolsPage.map((school, index) => {
            const diffLevel = getDifficultyLevel(school.difficulty_index);
            const levelClass = school.level.includes('985') ? 'level-985' :
                              school.level.includes('211') ? 'level-211' :
                              school.level.includes('双一流') ? 'level-双一流' : '';
            return '' +
                '<div class="school-card" data-index="' + index + '">' +
                    '<div class="school-card-header">' +
                        '<h4 class="school-name">' + school.name + '</h4>' +
                        '<span class="difficulty-badge difficulty-' + diffLevel + '" title="' + getDifficultyText(school.difficulty_index) + '">' + school.difficulty_index + '</span>' +
                    '</div>' +
                    '<div class="school-info-row">' +
                        '<span class="school-tag ' + levelClass + '">' + school.level + '</span>' +
                        '<span class="school-tag">学科评估：' + school.discipline + '</span>' +
                    '</div>' +
                    '<div class="school-directions"><strong>专业方向：</strong>' + school.directions.join('、') + '</div>' +
                    '<div class="school-exam"><strong>初试科目：</strong>' + school.exam_subjects.substring(0, 80) + (school.exam_subjects.length > 80 ? '...' : '') + '</div>' +
                    '<div class="school-score-line"><strong>近年复试线：</strong>' + school.score_lines + '</div>' +
                    '<div class="school-expand-hint">点击查看完整信息 ▼</div>' +
                    '<div class="school-detail">' +
                        '<div class="school-detail-section"><div class="school-detail-title">📚 参考书目</div><div class="school-detail-content">' + school.books + '</div></div>' +
                        '<div class="school-detail-section"><div class="school-detail-title">📝 复试内容</div><div class="school-detail-content">' + school.retest + '</div></div>' +
                        '<div class="school-detail-section"><div class="school-detail-title">📊 招生人数</div><div class="school-detail-content">' + school.enrollment + '</div></div>' +
                        '<div class="school-detail-section"><div class="school-detail-title">🏷️ 院校标签</div><div class="school-detail-content">' + school.tags.map(t => '<span class="school-tag">' + t + '</span>').join(' ') + '</div></div>' +
                        '<div class="school-detail-section"><div class="school-detail-title">📅 数据更新日期</div><div class="school-detail-content">' + (school.last_updated || '未知') + '</div></div>' +
                    '</div>' +
                '</div>';
        }).join('');

        listEl.innerHTML = html;

        listEl.querySelectorAll('.school-card').forEach(card => {
            card.addEventListener('click', () => {
                card.classList.toggle('expanded');
                const hint = card.querySelector('.school-expand-hint');
                if (card.classList.contains('expanded')) {
                    hint.textContent = '点击收起 ▲';
                } else {
                    hint.textContent = '点击查看完整信息 ▼';
                }
            });
        });
    }

    // 绑定双窗口事件
    function bindWindowEvents() {
        // 窗口切换标签（data-window 切换窗口，data-target 打开模态框）
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (tab.dataset.window) {
                    switchWindow(tab.dataset.window);
                } else if (tab.dataset.target === 'glossary') {
                    // 打开知识库模态框
                    if (typeof openGlossaryModal === 'function') {
                        openGlossaryModal();
                    } else {
                        const gModal = document.getElementById('glossaryModal');
                        if (gModal) {
                            gModal.classList.add('active');
                            document.body.style.overflow = 'hidden';
                        }
                    }
                } else if (tab.dataset.target === 'saved') {
                    // 打开收藏模态框
                    if (typeof openSavedModal === 'function') {
                        openSavedModal();
                    } else {
                        const sModal = document.getElementById('savedModal');
                        if (sModal) {
                            sModal.classList.add('active');
                            document.body.style.overflow = 'hidden';
                        }
                    }
                }
            });
        });

        // 省份卡片点击
        document.querySelectorAll('.province-card').forEach(card => {
            card.addEventListener('click', () => {
                if (card.classList.contains('is-locked')) {
                    return;
                }
                document.querySelectorAll('.province-card').forEach(c => c.classList.remove('is-active'));
                card.classList.add('is-active');
            });
        });

        // 高校考研页面筛选事件（层次/难度多选标签 + 排序按钮 + 搜索）
        function toggleFilterTags(selector, allSelector, activeSel) {
            document.querySelectorAll(selector).forEach((b) => {
                b.addEventListener('click', () => {
                    const v = b.dataset.level || b.dataset.diff;
                    if (v === 'all') {
                        // 点击"全部"：清除该组所有选中，仅保留"全部"
                        document.querySelectorAll(selector).forEach((x) => x.classList.remove('is-active'));
                        b.classList.add('is-active');
                    } else {
                        // 点击具体标签：切换选中
                        b.classList.toggle('is-active');
                        // 若选中了具体标签，取消"全部"
                        document.querySelectorAll(allSelector).forEach((x) => x.classList.remove('is-active'));
                        // 若没有任何具体标签选中，恢复"全部"
                        const any = document.querySelectorAll(activeSel).length;
                        if (any === 0) {
                            document.querySelectorAll(allSelector).forEach((x) => x.classList.add('is-active'));
                        }
                    }
                    filterSchoolsPage();
                });
            });
        }
        toggleFilterTags('.school-level-btn', '.school-level-btn[data-level="all"]', '.school-level-btn.is-active:not([data-level="all"])');
        toggleFilterTags('.school-diff-btn', '.school-diff-btn[data-diff="all"]', '.school-diff-btn.is-active:not([data-diff="all"])');
        // 排序按钮（单选，点击切换）
        document.querySelectorAll('.school-sort-btn').forEach((b) => {
            b.addEventListener('click', () => {
                document.querySelectorAll('.school-sort-btn').forEach((x) => x.classList.remove('is-active'));
                b.classList.add('is-active');
                filterSchoolsPage();
            });
        });
        const schoolsSearch2 = document.getElementById('schoolsSearch2');
        if (schoolsSearch2) schoolsSearch2.addEventListener('input', filterSchoolsPage);

        // 就业窗口"查看岗位详情/查看更多招聘"死链接修复：点击平滑滚动到对应区块
        document.querySelectorAll('.block-link').forEach((link, idx) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = idx === 0 ? 'jobsGrid' : 'recruitGrid';
                const el = document.getElementById(targetId);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    }

})();