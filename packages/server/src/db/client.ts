import Database from 'better-sqlite3';
import type { Database as SqliteDatabase } from 'better-sqlite3';
import { drizzle, type BetterSQLite3Database } from 'drizzle-orm/better-sqlite3';
import fs from 'node:fs';
import path from 'node:path';
import * as schema from './schema.js';

export type AppDb = BetterSQLite3Database<typeof schema>;

export function createDb(databaseUrl = process.env.DATABASE_URL ?? './data/opsswarm.db'): {
  db: AppDb;
  sqlite: SqliteDatabase;
} {
  const resolved =
    databaseUrl === ':memory:' ? ':memory:' : path.isAbsolute(databaseUrl) ? databaseUrl : path.resolve(databaseUrl);

  if (resolved !== ':memory:') {
    fs.mkdirSync(path.dirname(resolved), { recursive: true });
  }

  const sqlite = new Database(resolved);
  sqlite.pragma('journal_mode = WAL');
  sqlite.pragma('foreign_keys = ON');

  // Lightweight bootstrap migrations for the benchmark app.
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS runs (
      id TEXT PRIMARY KEY,
      idempotency_key TEXT,
      status TEXT NOT NULL,
      scenario_id TEXT NOT NULL,
      incident_json TEXT NOT NULL,
      options_json TEXT NOT NULL,
      report_json TEXT,
      error_message TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      started_at TEXT,
      finished_at TEXT,
      cancel_requested INTEGER NOT NULL DEFAULT 0
    );
    CREATE UNIQUE INDEX IF NOT EXISTS runs_idempotency_key_uidx ON runs(idempotency_key);

    CREATE TABLE IF NOT EXISTS steps (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL REFERENCES runs(id),
      name TEXT NOT NULL,
      status TEXT NOT NULL,
      attempt INTEGER NOT NULL DEFAULT 0,
      max_attempts INTEGER NOT NULL DEFAULT 3,
      output_json TEXT,
      error_message TEXT,
      token_prompt INTEGER NOT NULL DEFAULT 0,
      token_completion INTEGER NOT NULL DEFAULT 0,
      duration_ms INTEGER,
      started_at TEXT,
      finished_at TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS steps_run_id_idx ON steps(run_id);
    CREATE UNIQUE INDEX IF NOT EXISTS steps_run_name_uidx ON steps(run_id, name);

    CREATE TABLE IF NOT EXISTS step_attempts (
      id TEXT PRIMARY KEY,
      step_id TEXT NOT NULL REFERENCES steps(id),
      attempt INTEGER NOT NULL,
      status TEXT NOT NULL,
      is_repair INTEGER NOT NULL DEFAULT 0,
      input_json TEXT,
      output_json TEXT,
      error_message TEXT,
      token_prompt INTEGER NOT NULL DEFAULT 0,
      token_completion INTEGER NOT NULL DEFAULT 0,
      duration_ms INTEGER,
      started_at TEXT NOT NULL,
      finished_at TEXT
    );
    CREATE INDEX IF NOT EXISTS step_attempts_step_id_idx ON step_attempts(step_id);

    CREATE TABLE IF NOT EXISTS events (
      id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL REFERENCES runs(id),
      type TEXT NOT NULL,
      step_name TEXT,
      attempt INTEGER,
      message TEXT NOT NULL,
      payload_json TEXT,
      created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS events_run_id_idx ON events(run_id);
  `);

  const db = drizzle(sqlite, { schema });
  return { db, sqlite };
}
