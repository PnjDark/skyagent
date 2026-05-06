import { readFileSync } from 'fs'
import { join } from 'path'
import { Pool } from 'pg'
import { config } from 'dotenv'

config({ path: '.env.local' })

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
})

async function migrate() {
  const sql = readFileSync(join(process.cwd(), 'src/db/schema.sql'), 'utf8')
  const client = await pool.connect()
  try {
    console.log('Running migration...')
    await client.query(sql)
    console.log('✅ Schema applied to Neon successfully')
  } finally {
    client.release()
    await pool.end()
  }
}

migrate().catch(err => {
  console.error('❌ Migration failed:', err.message)
  process.exit(1)
})
