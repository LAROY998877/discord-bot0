const mongoose = require('mongoose');

// نموذج المستخدم
const userSchema = new mongoose.Schema({
    userId: { type: String, required: true, unique: true },
    isRegistered: { type: Boolean, default: false },
    name: { type: String, default: '' },
    age: { type: Number, default: 0 },
    gender: { type: String, default: '' },
    job: { type: String, default: '' }, // قاتل، طباخ، دكتور، مغامر، مزارع، حداد
    balance: { type: Number, default: 100 },
    titles: { type: [String], default: [] },
    activeTitle: { type: String, default: '' },
    inventory: [{
        name: String,
        type: String, // عتاد، أداة، إلخ
        stats: Object,
        equipped: { type: Boolean, default: false }
    }],
    guildId: { type: String, default: null },
    hero: { type: String, default: null },
    loan: {
        amount: { type: Number, default: 0 },
        dueDate: { type: Date, default: null }
    }
});

const User = mongoose.model('User', userSchema);

// نموذج النقابة
const guildSchema = new mongoose.Schema({
    name: { type: String, required: true, unique: true },
    leaderId: { type: String, required: true },
    members: { type: [String], default: [] },
    treasury: { type: Number, default: 0 }, // العملات المتبرع بها
    warehouse: [{
        name: String,
        type: String,
        stats: Object,
        donatedBy: String
    }]
});

const Guild = mongoose.model('Guild', guildSchema);

module.exports = { User, Guild };
