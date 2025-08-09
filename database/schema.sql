-- Smart Renamer Cloud Database Schema
-- This schema defines the tables for the Cloudflare D1 database

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    contact TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    client TEXT,
    status TEXT,
    start_date TEXT,
    end_date TEXT,
    builders_fee REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Team members table
CREATE TABLE IF NOT EXISTS team_members (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    card_last_four TEXT,
    title TEXT,
    department TEXT,
    email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    vendor TEXT NOT NULL,
    amount TEXT NOT NULL,
    description TEXT,
    transaction_type TEXT DEFAULT 'charge',
    created_at TEXT NOT NULL
);

-- Manual matches table (links files to transactions)
CREATE TABLE IF NOT EXISTS manual_matches (
    filename TEXT PRIMARY KEY,
    transaction_index INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- Reimbursements table
CREATE TABLE IF NOT EXISTS reimbursements (
    id INTEGER PRIMARY KEY,
    vendor TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Transaction tags table
CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_index INTEGER PRIMARY KEY,
    tags TEXT NOT NULL, -- JSON array of tags
    created_at TEXT NOT NULL
);

-- File metadata table
CREATE TABLE IF NOT EXISTS file_metadata (
    filename TEXT PRIMARY KEY,
    metadata TEXT NOT NULL, -- JSON object with file metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_team_members_name ON team_members(name);
CREATE INDEX IF NOT EXISTS idx_team_members_card ON team_members(card_last_four);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_vendor ON transactions(vendor);
CREATE INDEX IF NOT EXISTS idx_manual_matches_transaction ON manual_matches(transaction_index);
CREATE INDEX IF NOT EXISTS idx_reimbursements_date ON reimbursements(date);
CREATE INDEX IF NOT EXISTS idx_reimbursements_vendor ON reimbursements(vendor); 