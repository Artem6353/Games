/**
 * Gold Mining Clicker - Core Game Engine
 * Version 2.0 - Modular Architecture with Observer Pattern
 */

// ============================================
// EVENT EMITTER (Observer Pattern)
// ============================================
class EventEmitter {
    constructor() {
        this.events = {};
    }

    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
        return () => this.off(event, listener);
    }

    off(event, listener) {
        if (!this.events[event]) return;
        this.events[event] = this.events[event].filter(l => l !== listener);
    }

    emit(event, ...args) {
        if (!this.events[event]) return;
        this.events[event].forEach(listener => listener(...args));
    }

    once(event, listener) {
        const wrapper = (...args) => {
            this.off(event, wrapper);
            listener(...args);
        };
        return this.on(event, wrapper);
    }
}

// ============================================
// GAME CONSTANTS & CONFIGURATION
// ============================================
const CONFIG = {
    SAVE_KEY: 'goldMiningSave_v2',
    SAVE_VERSION: 2,
    SAVE_INTERVAL: 10000,
    AUTOSAVE_DEBOUNCE: 5000,
    FPS_TARGET: 60,
    OFFLINE_LIMIT: 86400000,
    PERFORMANCE_THRESHOLD: 30,
    
    // Number formatting rules
    NUMBER_FORMATTERS: [
        { limit: 1e3, suffix: '', decimals: 0 },
        { limit: 1e6, suffix: 'K', decimals: 1 },
        { limit: 1e9, suffix: 'M', decimals: 2 },
        { limit: 1e12, suffix: 'B', decimals: 2 },
        { limit: 1e15, suffix: 'T', decimals: 2 },
        { limit: 1e18, suffix: 'Qa', decimals: 2 },
        { limit: 1e21, suffix: 'Qi', decimals: 2 },
        { limit: 1e24, suffix: 'Sx', decimals: 2 },
        { limit: 1e27, suffix: 'Sp', decimals: 2 },
        { limit: Infinity, suffix: '+', decimals: 2 }
    ],

    // Combo system settings
    COMBO_WINDOW: 2000, // ms between clicks to maintain combo
    COMBO_MAX: 50,
    COMBO_MULTIPLIER_BASE: 0.02, // +2% per combo level

    // Mineral discovery chance
    MINERAL_CHANCE: 0.001, // 0.1% per click
};

// ============================================
// GAME DATA DEFINITIONS
// ============================================
const TOOLS = [
    { id: 'pickaxe_1', name: 'Каменная кирка', baseCost: 15, basePower: 1, description: 'Простая кирка для начала добычи', rarity: 'common' },
    { id: 'pickaxe_2', name: 'Железная кирка', baseCost: 100, basePower: 3, description: 'Надёжная кирка из железа', rarity: 'common' },
    { id: 'pickaxe_3', name: 'Золотая кирка', baseCost: 500, basePower: 8, description: 'Благородный инструмент', rarity: 'rare' },
    { id: 'drill_1', name: 'Ручной бур', baseCost: 2000, basePower: 20, description: 'Механизированное бурение', rarity: 'rare' },
    { id: 'drill_2', name: 'Алмазный бур', baseCost: 10000, basePower: 50, description: 'Сверхпрочное сверло', rarity: 'epic' },
    { id: 'laser_1', name: 'Лазерный резак', baseCost: 50000, basePower: 150, description: 'Высокотехнологичная добыча', rarity: 'epic' },
    { id: 'quantum_1', name: 'Квантовый экстрактор', baseCost: 1000000, basePower: 500, description: 'Добыча из параллельных реальностей', rarity: 'legendary' },
    { id: 'void_1', name: 'Пустотный сборщик', baseCost: 50000000, basePower: 2000, description: 'Извлекает энергию из пустоты', rarity: 'mythic' }
];

const MINERS = [
    { id: 'miner_1', name: 'Новичок', baseCost: 25, baseGPS: 1, description: 'Начинающий шахтёр', rarity: 'common' },
    { id: 'miner_2', name: 'Опытный шахтёр', baseCost: 150, baseGPS: 5, description: 'Профессионал своего дела', rarity: 'common' },
    { id: 'miner_3', name: 'Ветеран', baseCost: 750, baseGPS: 15, description: 'Многолетний опыт', rarity: 'rare' },
    { id: 'miner_4', name: 'Мастер', baseCost: 4000, baseGPS: 40, description: 'Элита добычи', rarity: 'rare' },
    { id: 'miner_5', name: 'Легенда', baseCost: 20000, baseGPS: 100, description: 'Живая легенда шахты', rarity: 'epic' },
    { id: 'miner_6', name: 'Герой шахты', baseCost: 100000, baseGPS: 300, description: 'Непревзойдённый мастер', rarity: 'legendary' }
];

const ENGINEERS = [
    { id: 'engineer_1', name: 'Техник', baseCost: 500, baseGPS: 10, description: 'Обслуживает оборудование', rarity: 'common' },
    { id: 'engineer_2', name: 'Инженер', baseCost: 3000, baseGPS: 30, description: 'Оптимизирует процессы', rarity: 'rare' },
    { id: 'engineer_3', name: 'Главный инженер', baseCost: 15000, baseGPS: 80, description: 'Руководит всеми системами', rarity: 'epic' },
    { id: 'engineer_4', name: 'Техногений', baseCost: 75000, baseGPS: 200, description: 'Гений автоматизации', rarity: 'legendary' },
    { id: 'engineer_5', name: 'ИИ Архитектор', baseCost: 500000, baseGPS: 600, description: 'Искусственный интеллект', rarity: 'mythic' }
];

const BUILDINGS = [
    { id: 'elevator_1', name: 'Грузовой лифт', baseCost: 1000, baseGPS: 25, description: 'Быстрая доставка руды', rarity: 'common' },
    { id: 'sorter_1', name: 'Сортировочная линия', baseCost: 5000, baseGPS: 60, description: 'Автоматическая сортировка', rarity: 'rare' },
    { id: 'smelter_1', name: 'Плавильня', baseCost: 25000, baseGPS: 150, description: 'Переплавка руды в слитки', rarity: 'rare' },
    { id: 'refinery_1', name: 'Аффинажный завод', baseCost: 100000, baseGPS: 400, description: 'Очистка до 99.99%', rarity: 'epic' },
    { id: 'vault_1', name: 'Золотохранилище', baseCost: 500000, baseGPS: 1000, description: 'Надёжное хранение', rarity: 'epic' },
    { id: 'fusion_1', name: 'Термоядерный реактор', baseCost: 5000000, baseGPS: 5000, description: 'Энергия будущего', rarity: 'legendary' },
    { id: 'dyson_1', name: 'Сфера Дайсона', baseCost: 100000000, baseGPS: 50000, description: 'Энергия звезды', rarity: 'mythic' }
];

const RESEARCH_TREE = {
    mining: {
        name: 'Добыча',
        icon: '⛏️',
        technologies: [
            { id: 'mining_1', name: 'Геологоразведка', cost: 500, description: '+20% ко всей добыче', effect: { type: 'global_mult', value: 0.2 }, prerequisites: [] },
            { id: 'mining_2', name: 'Глубинное бурение', cost: 2500, description: '+50% ко всей добыче', effect: { type: 'global_mult', value: 0.5 }, prerequisites: ['mining_1'] },
            { id: 'mining_3', name: 'Сейсмический сканер', cost: 10000, description: '+100% ко всей добыче', effect: { type: 'global_mult', value: 1.0 }, prerequisites: ['mining_2'] },
            { id: 'mining_4', name: 'Термоядерный бур', cost: 50000, description: '+250% ко всей добыче', effect: { type: 'global_mult', value: 2.5 }, prerequisites: ['mining_3'] },
            { id: 'mining_5', name: 'Квантовая добыча', cost: 500000, description: '+500% ко всей добыче', effect: { type: 'global_mult', value: 5.0 }, prerequisites: ['mining_4'] }
        ]
    },
    automation: {
        name: 'Автоматизация',
        icon: '⚙️',
        technologies: [
            { id: 'auto_1', name: 'Конвейерная лента', cost: 750, description: '+25% к GPS персонала', effect: { type: 'gps_mult', value: 0.25 }, prerequisites: [] },
            { id: 'auto_2', name: 'Роботизация', cost: 5000, description: '+50% к GPS персонала', effect: { type: 'gps_mult', value: 0.5 }, prerequisites: ['auto_1'] },
            { id: 'auto_3', name: 'ИИ управление', cost: 25000, description: '+100% к GPS персонала', effect: { type: 'gps_mult', value: 1.0 }, prerequisites: ['auto_2'] },
            { id: 'auto_4', name: 'Наноассемблеры', cost: 100000, description: '+200% к GPS персонала', effect: { type: 'gps_mult', value: 2.0 }, prerequisites: ['auto_3'] },
            { id: 'auto_5', name: 'Полная автономия', cost: 1000000, description: '+400% к GPS персонала', effect: { type: 'gps_mult', value: 4.0 }, prerequisites: ['auto_4'] }
        ]
    },
    economy: {
        name: 'Экономика',
        icon: '💰',
        technologies: [
            { id: 'econ_1', name: 'Оптимизация затрат', cost: 1000, description: '-10% к стоимости улучшений', effect: { type: 'cost_reduction', value: 0.1 }, prerequisites: [] },
            { id: 'econ_2', name: 'Рыночные связи', cost: 7500, description: '-20% к стоимости улучшений', effect: { type: 'cost_reduction', value: 0.2 }, prerequisites: ['econ_1'] },
            { id: 'econ_3', name: 'Монополия', cost: 30000, description: '-30% к стоимости улучшений', effect: { type: 'cost_reduction', value: 0.3 }, prerequisites: ['econ_2'] },
            { id: 'econ_4', name: 'Финансовая империя', cost: 150000, description: '-40% к стоимости улучшений', effect: { type: 'cost_reduction', value: 0.4 }, prerequisites: ['econ_3'] },
            { id: 'econ_5', name: 'Галактическая торговля', cost: 2000000, description: '-50% к стоимости улучшений', effect: { type: 'cost_reduction', value: 0.5 }, prerequisites: ['econ_4'] }
        ]
    },
    prestige: {
        name: 'Вечность',
        icon: '💎',
        technologies: [
            { id: 'prestige_1', name: 'Сущность времени', cost: 1000000, description: '+50% к бонусу престижа', effect: { type: 'prestige_mult', value: 0.5 }, prerequisites: [] },
            { id: 'prestige_2', name: 'Временной поток', cost: 10000000, description: '+100% к бонусу престижа', effect: { type: 'prestige_mult', value: 1.0 }, prerequisites: ['prestige_1'] },
            { id: 'prestige_3', name: 'Вечность', cost: 100000000, description: '+200% к бонусу престижа', effect: { type: 'prestige_mult', value: 2.0 }, prerequisites: ['prestige_2'] }
        ]
    }
};

const ACHIEVEMENTS = [
    { id: 'first_gold', name: 'Первое золото', description: 'Добудьте первое золото', condition: (state) => state.stats.totalMined >= 1, icon: '🥇', reward: 0 },
    { id: 'hundred_clicks', name: 'Упорство', description: 'Сделайте 100 кликов', condition: (state) => state.stats.totalClicks >= 100, icon: '💪', reward: 0 },
    { id: 'thousand_gold', name: 'Первая тысяча', description: 'Добудьте 1,000 золота', condition: (state) => state.stats.totalMined >= 1000, icon: '📦', reward: 100 },
    { id: 'first_upgrade', name: 'Прогресс', description: 'Купите первое улучшение', condition: (state) => state.stats.upgradesPurchased >= 1, icon: '⬆️', reward: 0 },
    { id: 'ten_upgrades', name: 'Коллекционер', description: 'Купите 10 улучшений', condition: (state) => state.stats.upgradesPurchased >= 10, icon: '🎯', reward: 500 },
    { id: 'million_gold', name: 'Миллионер', description: 'Добудьте 1,000,000 золота', condition: (state) => state.stats.totalMined >= 1000000, icon: '💎', reward: 10000 },
    { id: 'first_prestige', name: 'Возрождение', description: 'Совершите первый престиж', condition: (state) => state.prestige.count > 0, icon: '🔄', reward: 0 },
    { id: 'billion_gold', name: 'Миллиардер', description: 'Добудьте 1,000,000,000 золота', condition: (state) => state.stats.totalMined >= 1000000000, icon: '👑', reward: 1000000 },
    { id: 'combo_master', name: 'Комбо-мастер', description: 'Достигните комбо x25', condition: (state) => state.combo.max >= 25, icon: '🔥', reward: 50000 },
    { id: 'mineral_hunter', name: 'Охотник за минералами', description: 'Найдите 10 минералов', condition: (state) => state.stats.mineralsFound >= 10, icon: '💠', reward: 100000 }
];

const EVENTS_POOL = [
    { id: 'gold_rush', name: 'Золотая лихорадка!', description: 'x3 ко всей добыче', duration: 30000, effect: { type: 'global_mult', value: 3.0 }, icon: '🌟', weight: 3 },
    { id: 'market_boom', name: 'Рыночный бум', description: 'x2 ко всей добыче', duration: 45000, effect: { type: 'global_mult', value: 2.0 }, icon: '📈', weight: 4 },
    { id: 'equipment_bonus', name: 'Бонус оборудования', description: '+50% к силе клика', duration: 25000, effect: { type: 'click_mult', value: 1.5 }, icon: '🔧', weight: 4 },
    { id: 'cave_in', name: 'Обвал!', description: '-50% к добыче', duration: 20000, effect: { type: 'global_mult', value: 0.5 }, icon: '⚠️', weight: 1 },
    { id: 'cosmic_blessing', name: 'Космическое благословение', description: 'x5 ко всей добыче', duration: 15000, effect: { type: 'global_mult', value: 5.0 }, icon: '✨', weight: 1 }
];

const MINERALS = [
    { id: 'amber', name: 'Янтарь', icon: '🟡', bonus: 100, chance: 0.4, description: '+100 золота' },
    { id: 'ruby', name: 'Рубин', icon: '❤️', bonus: 500, chance: 0.25, description: '+500 золота' },
    { id: 'sapphire', name: 'Сапфир', icon: '💙', bonus: 1000, chance: 0.15, description: '+1000 золота' },
    { id: 'emerald', name: 'Изумруд', icon: '💚', bonus: 2500, chance: 0.1, description: '+2500 золота' },
    { id: 'diamond', name: 'Алмаз', icon: '💎', bonus: 10000, chance: 0.07, description: '+10000 золота' },
    { id: 'void_crystal', name: 'Кристалл Пустоты', icon: '🔮', bonus: 50000, chance: 0.02, description: '+50000 золота' },
    { id: 'eternity_shard', name: 'Осколок Вечности', icon: '⭐', bonus: 100000, chance: 0.01, description: '+100000 золота' }
];

// Export for use in other modules
window.GameData = {
    CONFIG,
    TOOLS,
    MINERS,
    ENGINEERS,
    BUILDINGS,
    RESEARCH_TREE,
    ACHIEVEMENTS,
    EVENTS_POOL,
    MINERALS
};
