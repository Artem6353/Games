/**
 * Gold Mining Clicker - Main Game Engine v2.0
 */

const Game = {
    state: null,
    lastUpdate: Date.now(),
    running: false,

    init() {
        console.log('🎮 Gold Mining Clicker v2.0 initializing...');
        this.loadGame();
        UI.init();
        Particles.init();
        this.setupEventListeners();
        this.renderAll();
        this.processOfflineProgress();
        this.running = true;
        this.gameLoop();
        setInterval(() => this.saveGame(), CONFIG.SAVE_INTERVAL);
        setTimeout(() => UI.hideLoading(), 500);
        console.log('✅ Game initialized!');
    },

    loadGame() {
        const savedData = Helpers.storage.get(CONFIG.SAVE_KEY);
        if (savedData && Calculator.validateSaveData(savedData)) {
            this.state = savedData;
            Calculator.initializeCounts(this.state);
            this.state.lastOnline = Date.now();
            console.log('💾 Save loaded');
        } else {
            this.state = Calculator.createInitialState();
            console.log('🆕 New game created');
        }
    },

    saveGame(showIndicator = true) {
        if (!this.state) return;
        this.state.lastSave = Date.now();
        if (showIndicator) UI.showSaveIndicator(true);
        const success = Helpers.storage.set(CONFIG.SAVE_KEY, this.state);
        if (success && showIndicator) setTimeout(() => UI.showSaveIndicator(false), 1000);
        return success;
    },

    processOfflineProgress() {
        const offlineTime = Date.now() - this.state.lastSave;
        if (offlineTime > 60000) {
            const gps = Calculator.calculateGPS(this.state);
            const earnings = gps * (offlineTime / 1000);
            if (earnings > 0) {
                this.state.gold += earnings;
                this.state.totalMined += earnings;
                setTimeout(() => alert('Оффлайн доход: ' + Calculator.formatNumber(earnings)), 1000);
            }
        }
    },

    setupEventListeners() {
        const mineBtn = document.getElementById('mineButton');
        if (mineBtn) {
            mineBtn.addEventListener('click', (e) => this.handleMineClick(e));
            mineBtn.addEventListener('touchstart', (e) => { e.preventDefault(); this.handleMineClick(e.touches[0]); }, { passive: false });
            mineBtn.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.handleMineClick(e); } });
        }

        document.getElementById('settingsBtn')?.addEventListener('click', () => UI.showModal('settingsModal'));
        document.getElementById('closeSettingsBtn')?.addEventListener('click', () => UI.hideModal('settingsModal'));
        document.getElementById('statsBtn')?.addEventListener('click', () => this.showStatsModal());
        document.getElementById('closeStatsBtn')?.addEventListener('click', () => UI.hideModal('statsModal'));
        document.getElementById('prestigeBtn')?.addEventListener('click', () => this.showPrestigeModal());
        document.getElementById('cancelPrestigeBtn')?.addEventListener('click', () => UI.hideModal('prestigeModal'));
        document.getElementById('confirmPrestigeBtn')?.addEventListener('click', () => this.doPrestige());
        document.getElementById('mineralCloseBtn')?.addEventListener('click', () => UI.hideMineralPopup());

        document.getElementById('perfModeToggle')?.addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
            Particles.setEnabled(!e.currentTarget.classList.contains('active'));
        });

        document.getElementById('floatingTextToggle')?.addEventListener('click', (e) => e.currentTarget.classList.toggle('active'));
        document.getElementById('exportSaveBtn')?.addEventListener('click', () => this.exportSave());
        document.getElementById('importSaveBtn')?.addEventListener('click', () => this.importSave());
        document.getElementById('resetSaveBtn')?.addEventListener('click', () => { if (confirm('Сбросить прогресс?')) this.resetGame(); });

        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => { if (e.target === modal) { modal.classList.remove('active'); document.body.style.overflow = ''; } });
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
                document.body.style.overflow = '';
            }
        });
    },

    handleMineClick(e) {
        const now = Date.now();
        const mineBtn = document.getElementById('mineButton');
        const timeSinceLastClick = now - this.state.combo.lastClick;
        
        if (timeSinceLastClick < CONFIG.COMBO_WINDOW) {
            this.state.combo.current = Math.min(this.state.combo.current + 1, CONFIG.COMBO_MAX);
        } else {
            this.state.combo.current = 1;
        }
        this.state.combo.lastClick = now;
        this.state.combo.max = Math.max(this.state.combo.max, this.state.combo.current);

        const power = Calculator.calculateClickPower(this.state);
        let earnings = power;
        const isCrit = Math.random() < (0.05 + this.state.prestige.bonus * 0.001);
        
        if (isCrit) earnings *= 2;

        this.state.gold += earnings;
        this.state.totalMined += earnings;
        this.state.stats.totalClicks++;

        const rect = mineBtn.getBoundingClientRect();
        const x = e.clientX || (rect.left + rect.width / 2);
        const y = e.clientY || (rect.top + rect.height / 2);

        Particles.spawnGold(x, y);

        if (document.getElementById('floatingTextToggle')?.classList.contains('active')) {
            UI.showFloatingText(x, y, isCrit ? '+' + Calculator.formatNumber(earnings) + ' КРИТ!' : '+' + Calculator.formatNumber(earnings), isCrit ? 'crit' : 'normal');
        }

        this.checkMineralDiscovery();
        UI.updateCombo(this.state.combo);
        mineBtn.classList.add('clicked');
        setTimeout(() => mineBtn.classList.remove('clicked'), 100);
        this.updateUI();
    },

    checkMineralDiscovery() {
        if (Math.random() > CONFIG.MINERAL_CHANCE) return;
        const mineral = Helpers.weightedRandom(MINERALS, 'chance');
        if (mineral) {
            this.state.gold += mineral.bonus;
            this.state.totalMined += mineral.bonus;
            this.state.stats.mineralsFound++;
            UI.showMineralPopup(mineral);
            Particles.spawnExplosion(window.innerWidth / 2, window.innerHeight / 2);
            UI.showNotification('Найден ' + mineral.name + '! +' + Calculator.formatNumber(mineral.bonus), 'success');
        }
    },

    buyUpgrade(type, id) {
        const collections = { tools: TOOLS, miners: MINERS, engineers: ENGINEERS, buildings: BUILDINGS };
        const item = collections[type].find(i => i.id === id);
        if (!item) return;

        const level = this.state[type][id] || 0;
        const cost = Calculator.calculateCost(item.baseCost, level, Calculator.getCostReduction(this.state));

        if (this.state.gold >= cost) {
            this.state.gold -= cost;
            this.state[type][id] = level + 1;
            this.state.stats.upgradesPurchased++;
            UI.showNotification('Куплено: ' + item.name, 'success');
            this.renderUpgrades();
            this.updateUI();
            this.saveGame(false);
        }
    },

    researchTech(techId) {
        if (!Calculator.canResearch(this.state, techId)) return;
        let tech = null;
        for (const branch of Object.values(RESEARCH_TREE)) {
            tech = branch.technologies.find(t => t.id === techId);
            if (tech) break;
        }
        if (!tech || this.state.gold < tech.cost) return;

        this.state.gold -= tech.cost;
        this.state.research.push(techId);
        UI.showNotification('Исследовано: ' + tech.name, 'success');
        this.renderResearch();
        this.updateUI();
        this.saveGame(false);
    },

    showPrestigeModal() {
        const gain = Calculator.calculatePrestigeGain(this.state);
        if (gain <= 0) { UI.showNotification('Нужно больше золота для престижа!', 'warning'); return; }
        document.getElementById('prestigeGainDisplay').textContent = gain;
        document.getElementById('currentPrestigeBonus').textContent = '+' + (this.state.prestige.bonus * 10).toFixed(0) + '%';
        document.getElementById('newPrestigeBonus').textContent = '+' + ((this.state.prestige.count + gain) * 10).toFixed(0) + '%';
        document.getElementById('prestigeIncrease').textContent = '+' + (gain * 10).toFixed(0) + '%';
        UI.showModal('prestigeModal');
    },

    doPrestige() {
        const gain = Calculator.calculatePrestigeGain(this.state);
        if (gain <= 0) return;
        const oldCount = this.state.prestige.count;
        const oldAchievements = [...this.state.achievements];
        this.state = Calculator.createInitialState();
        this.state.prestige.count = oldCount + gain;
        this.state.prestige.bonus = this.state.prestige.count;
        this.state.achievements = oldAchievements;
        UI.hideModal('prestigeModal');
        UI.showNotification('Престиж! +' + gain + ' Слитков Вечности', 'success');
        this.renderAll();
        this.saveGame();
    },

    exportSave() {
        const code = btoa(JSON.stringify(this.state));
        Helpers.copyToClipboard(code);
        UI.showNotification('Сохранение скопировано!', 'success');
    },

    importSave() {
        const code = prompt('Вставьте код сохранения:');
        if (!code) return;
        try {
            const data = JSON.parse(atob(code));
            if (Calculator.validateSaveData(data)) {
                this.state = data;
                this.renderAll();
                this.saveGame();
                UI.showNotification('Сохранение загружено!', 'success');
            }
        } catch (e) { UI.showNotification('Ошибка импорта', 'error'); }
    },

    resetGame() {
        Helpers.storage.remove(CONFIG.SAVE_KEY);
        this.state = Calculator.createInitialState();
        this.renderAll();
        this.saveGame();
        UI.showNotification('Прогресс сброшен', 'info');
    },

    showStatsModal() {
        const s = this.state.stats;
        document.getElementById('statsContent').innerHTML = '<div class="stats-panel">' +
            '<div class="stat-row"><span>Всего добыто:</span><span>' + Calculator.formatNumber(s.totalMined) + '</span></div>' +
            '<div class="stat-row"><span>Кликов:</span><span>' + Calculator.formatNumber(s.totalClicks) + '</span></div>' +
            '<div class="stat-row"><span>Время игры:</span><span>' + Calculator.formatTime(s.playTime * 1000) + '</span></div>' +
            '<div class="stat-row"><span>Улучшений:</span><span>' + s.upgradesPurchased + '</span></div>' +
            '<div class="stat-row"><span>Минералов:</span><span>' + s.mineralsFound + '</span></div>' +
            '<div class="stat-row"><span>Макс комбо:</span><span>x' + this.state.combo.max + '</span></div>' +
            '<div class="stat-row"><span>Престижей:</span><span>' + this.state.prestige.count + '</span></div></div>';
        UI.showModal('statsModal');
    },

    renderAll() {
        this.renderUpgrades();
        this.renderResearch();
        this.renderAchievements();
        this.updateUI();
    },

    renderUpgrades() {
        const cr = Calculator.getCostReduction(this.state);
        document.getElementById('toolsGrid').innerHTML = TOOLS.map(t => UI.renderUpgradeCard(t, this.state.tools[t.id]||0, Calculator.calculateCost(t.baseCost, this.state.tools[t.id]||0, cr), this.state.gold >= Calculator.calculateCost(t.baseCost, this.state.tools[t.id]||0, cr))).join('');
        document.getElementById('minersGrid').innerHTML = MINERS.map(m => UI.renderUpgradeCard(m, this.state.miners[m.id]||0, Calculator.calculateCost(m.baseCost, this.state.miners[m.id]||0, cr), this.state.gold >= Calculator.calculateCost(m.baseCost, this.state.miners[m.id]||0, cr))).join('');
        document.getElementById('engineersGrid').innerHTML = ENGINEERS.map(e => UI.renderUpgradeCard(e, this.state.engineers[e.id]||0, Calculator.calculateCost(e.baseCost, this.state.engineers[e.id]||0, cr), this.state.gold >= Calculator.calculateCost(e.baseCost, this.state.engineers[e.id]||0, cr))).join('');
        document.getElementById('buildingsGrid').innerHTML = BUILDINGS.map(b => UI.renderUpgradeCard(b, this.state.buildings[b.id]||0, Calculator.calculateCost(b.baseCost, this.state.buildings[b.id]||0, cr), this.state.gold >= Calculator.calculateCost(b.baseCost, this.state.buildings[b.id]||0, cr))).join('');
        this.setupUpgradeClickHandlers();
    },

    setupUpgradeClickHandlers() {
        document.querySelectorAll('.upgrade-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                if (TOOLS.find(t => t.id === id)) this.buyUpgrade('tools', id);
                else if (MINERS.find(m => m.id === id)) this.buyUpgrade('miners', id);
                else if (ENGINEERS.find(e => e.id === id)) this.buyUpgrade('engineers', id);
                else if (BUILDINGS.find(b => b.id === id)) this.buyUpgrade('buildings', id);
            });
        });
    },

    renderResearch() {
        let html = '';
        for (const [key, branch] of Object.entries(RESEARCH_TREE)) {
            html += '<div class="research-branch"><div class="branch-title">' + branch.icon + ' ' + branch.name + '</div>' + branch.technologies.map(t => UI.renderResearchNode(t, this.state)).join('') + '</div>';
        }
        document.getElementById('researchTree').innerHTML = html;
        document.getElementById('researchTree').querySelectorAll('.research-node:not(.locked):not(.researched)').forEach(node => {
            node.addEventListener('click', () => this.researchTech(node.dataset.id));
        });
    },

    renderAchievements() {
        ACHIEVEMENTS.forEach(ach => {
            if (!this.state.achievements.includes(ach.id) && ach.condition(this.state)) {
                this.state.achievements.push(ach.id);
                UI.showNotification('Достижение: ' + ach.name, 'success');
                if (ach.reward > 0) { this.state.gold += ach.reward; UI.showNotification('+' + Calculator.formatNumber(ach.reward) + ' золота', 'success'); }
            }
        });
        document.getElementById('achievementsList').innerHTML = ACHIEVEMENTS.slice(0, 5).map(ach => UI.renderAchievement(ach, this.state.achievements.includes(ach.id))).join('');
    },

    updateUI() {
        UI.updateGold(this.state.gold);
        UI.updateGPS(Calculator.calculateGPS(this.state));
        UI.updateClickPower(Calculator.calculateClickPower(this.state));
        UI.updateGlobalMultiplier(Calculator.calculateGlobalMultiplier(this.state));
        UI.updateStats(this.state.stats);
        UI.updatePrestige(this.state.prestige.count, this.state.prestige.bonus);
        this.renderUpgrades();
        this.renderResearch();
        this.renderAchievements();
        if (this.state.activeEvent && this.state.activeEvent.endTime <= Date.now()) { this.state.activeEvent = null; UI.renderEvent(null); }
    },

    triggerRandomEvent() {
        if (this.state.activeEvent) return;
        const event = Helpers.weightedRandom(EVENTS_POOL, 'weight');
        if (event) {
            this.state.activeEvent = Object.assign({}, event, { endTime: Date.now() + event.duration });
            UI.renderEvent(event);
            UI.showNotification(event.icon + ' ' + event.name + '!', 'info');
            setTimeout(() => { if (this.state.activeEvent && this.state.activeEvent.id === event.id) { this.state.activeEvent = null; UI.renderEvent(null); } }, event.duration);
        }
    },

    gameLoop() {
        if (!this.running) return;
        const now = Date.now();
        const dt = (now - this.lastUpdate) / 1000;
        this.lastUpdate = now;

        const gps = Calculator.calculateGPS(this.state);
        if (gps > 0 && dt > 0) {
            const earnings = gps * dt;
            this.state.gold += earnings;
            this.state.totalMined += earnings;
        }
        this.state.stats.playTime += dt;

        if (Math.random() < 0.0005) this.triggerRandomEvent();
        this.updateUI();
        requestAnimationFrame(() => this.gameLoop());
    }
};

window.Game = Game;
