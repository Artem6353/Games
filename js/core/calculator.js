/**
 * Gold Mining Clicker - Calculation Engine
 * Handles all game math and calculations
 */

const Calculator = {
    /**
     * Format number with suffixes (K, M, B, etc.)
     */
    formatNumber(num) {
        if (typeof num === 'bigint') {
            num = Number(num);
        }
        
        if (num < 0) return '-' + this.formatNumber(-num);
        if (num < 1000) return Math.floor(num).toString();
        
        for (let formatter of CONFIG.NUMBER_FORMATTERS) {
            if (num < formatter.limit) {
                const scaled = num / (formatter.limit / 1000);
                return scaled.toFixed(formatter.decimals).replace(/\.?0+$/, '') + formatter.suffix;
            }
        }
        
        return num.toExponential(2);
    },

    /**
     * Format time in milliseconds to readable string
     */
    formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    },

    /**
     * Calculate upgrade cost with exponential scaling
     */
    calculateCost(baseCost, level, costReduction = 0) {
        const multiplier = 1.15;
        const cost = baseCost * Math.pow(multiplier, level);
        return Math.max(1, Math.floor(cost * (1 - costReduction)));
    },

    /**
     * Calculate click power based on state
     */
    calculateClickPower(state) {
        let power = 1;

        // Add tool bonuses
        TOOLS.forEach(tool => {
            const level = state.tools[tool.id] || 0;
            power += tool.basePower * level;
        });

        // Apply research bonuses
        state.research.forEach(researchId => {
            for (const branch of Object.values(RESEARCH_TREE)) {
                const tech = branch.technologies.find(t => t.id === researchId);
                if (tech && tech.effect.type === 'global_mult') {
                    power *= (1 + tech.effect.value);
                }
            }
        });

        // Apply prestige bonus
        power *= (1 + state.prestige.bonus * 0.1);

        // Apply combo bonus
        if (state.combo.current > 0) {
            power *= (1 + state.combo.current * CONFIG.COMBO_MULTIPLIER_BASE);
        }

        // Apply event bonuses
        if (state.activeEvent && state.activeEvent.effect.type === 'click_mult') {
            power *= state.activeEvent.effect.value;
        }

        // Apply global event bonuses
        if (state.activeEvent && state.activeEvent.effect.type === 'global_mult') {
            power *= state.activeEvent.effect.value;
        }

        return Math.max(1, power);
    },

    /**
     * Calculate Gold Per Second (GPS)
     */
    calculateGPS(state) {
        let gps = 0;

        // Miners GPS
        MINERS.forEach(miner => {
            const level = state.miners[miner.id] || 0;
            gps += miner.baseGPS * level;
        });

        // Engineers GPS
        ENGINEERS.forEach(engineer => {
            const level = state.engineers[engineer.id] || 0;
            gps += engineer.baseGPS * level;
        });

        // Buildings GPS
        BUILDINGS.forEach(building => {
            const level = state.buildings[building.id] || 0;
            gps += building.baseGPS * level;
        });

        // Apply research bonuses
        state.research.forEach(researchId => {
            for (const branch of Object.values(RESEARCH_TREE)) {
                const tech = branch.technologies.find(t => t.id === researchId);
                if (tech && tech.effect.type === 'gps_mult') {
                    gps *= (1 + tech.effect.value);
                }
                if (tech && tech.effect.type === 'global_mult') {
                    gps *= (1 + tech.effect.value);
                }
            }
        });

        // Apply prestige bonus
        gps *= (1 + state.prestige.bonus * 0.1);

        // Apply event bonuses
        if (state.activeEvent && state.activeEvent.effect.type === 'global_mult') {
            gps *= state.activeEvent.effect.value;
        }

        return gps;
    },

    /**
     * Get total cost reduction from research
     */
    getCostReduction(state) {
        let reduction = 0;

        state.research.forEach(researchId => {
            for (const branch of Object.values(RESEARCH_TREE)) {
                const tech = branch.technologies.find(t => t.id === researchId);
                if (tech && tech.effect.type === 'cost_reduction') {
                    reduction = Math.max(reduction, tech.effect.value);
                }
            }
        });

        return reduction;
    },

    /**
     * Calculate prestige gain
     */
    calculatePrestigeGain(state) {
        if (state.totalMined < 1000000) return 0;
        
        let gain = Math.floor(Math.sqrt(state.totalMined / 1000000));
        
        // Apply prestige research bonuses
        state.research.forEach(researchId => {
            for (const branch of Object.values(RESEARCH_TREE)) {
                const tech = branch.technologies.find(t => t.id === researchId);
                if (tech && tech.effect.type === 'prestige_mult') {
                    gain = Math.floor(gain * (1 + tech.effect.value));
                }
            }
        });
        
        return Math.max(0, gain - state.prestige.count);
    },

    /**
     * Calculate global multiplier
     */
    calculateGlobalMultiplier(state) {
        let mult = 1;
        
        // Prestige bonus
        mult *= (1 + state.prestige.bonus * 0.1);
        
        // Research bonuses
        state.research.forEach(researchId => {
            for (const branch of Object.values(RESEARCH_TREE)) {
                const tech = branch.technologies.find(t => t.id === researchId);
                if (tech && tech.effect.type === 'global_mult') {
                    mult *= (1 + tech.effect.value);
                }
            }
        });
        
        // Event bonuses
        if (state.activeEvent && state.activeEvent.effect.type === 'global_mult') {
            mult *= state.activeEvent.effect.value;
        }
        
        return mult;
    },

    /**
     * Check if technology prerequisites are met
     */
    canResearch(state, techId) {
        let tech = null;
        for (const branch of Object.values(RESEARCH_TREE)) {
            tech = branch.technologies.find(t => t.id === techId);
            if (tech) break;
        }

        if (!tech) return false;
        if (state.research.includes(techId)) return false;
        
        const prerequisitesMet = tech.prerequisites.every(p => 
            state.research.includes(p)
        );

        return prerequisitesMet;
    },

    /**
     * Safe JSON parsing with fallback
     */
    safeJSONParse(str, defaultValue) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.warn('Failed to parse JSON:', e);
            return defaultValue;
        }
    },

    /**
     * Create initial game state
     */
    createInitialState() {
        return {
            gold: 0,
            totalMined: 0,
            prestige: {
                count: 0,
                bonus: 0
            },
            tools: {},
            miners: {},
            engineers: {},
            buildings: {},
            research: [],
            achievements: [],
            stats: {
                totalClicks: 0,
                totalMined: 0,
                upgradesPurchased: 0,
                playTime: 0,
                startTime: Date.now(),
                mineralsFound: 0
            },
            settings: {
                performanceMode: false,
                soundEnabled: true
            },
            combo: {
                current: 0,
                max: 0,
                lastClick: 0
            },
            mineSkin: 'default',
            lastSave: Date.now(),
            lastOnline: Date.now(),
            version: CONFIG.SAVE_VERSION
        };
    },

    /**
     * Initialize upgrade counts to 0 if not present
     */
    initializeCounts(state) {
        TOOLS.forEach(t => { if (state.tools[t.id] === undefined) state.tools[t.id] = 0; });
        MINERS.forEach(m => { if (state.miners[m.id] === undefined) state.miners[m.id] = 0; });
        ENGINEERS.forEach(e => { if (state.engineers[e.id] === undefined) state.engineers[e.id] = 0; });
        BUILDINGS.forEach(b => { if (state.buildings[b.id] === undefined) state.buildings[b.id] = 0; });
        
        // Initialize combo if not present
        if (!state.combo) {
            state.combo = { current: 0, max: 0, lastClick: 0 };
        }
        
        // Initialize minerals found stat
        if (!state.stats.mineralsFound) {
            state.stats.mineralsFound = 0;
        }
    },

    /**
     * Validate save data
     */
    validateSaveData(data) {
        if (!data || typeof data !== 'object') return false;
        if (data.version && data.version < 1) return false;
        if (isNaN(data.gold) || data.gold < 0) return false;
        return true;
    }
};

window.Calculator = Calculator;
