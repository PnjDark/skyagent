# Penjy OS Implementation Plan
## From Zero to Working Agent in 4 Phases

---

## PHASE 0: Setup (Days 1-2)
**Goal:** Establish the infrastructure plumbing. This is boring but non-negotiable.

### 0.1 Create Railway Project
```bash
# What you're doing:
# - Creating the compute layer where your agent lives
# - Setting up auto-sleep to keep costs near $0

Steps:
1. Go to railway.app
2. Create new project "sky-agent"
3. Connect GitHub repo (create one if you don't have it)
4. Set per-second billing (default)
5. Create 3 environments: dev, staging, production
```

**Output:** Railway project with git integration ready

---

### 0.2 Create Neon Database
```bash
# What you're doing:
# - Setting up your single source of truth
# - Creating the schema that everything reads from

Steps:
1. Go to neon.tech
2. Create project "sky-memory"
3. Create database "skydb"
4. Get connection string (keep it secret)

Initial Schema (we'll refine this):
```sql
-- Projects (auto-discovered from GitHub)
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_name TEXT NOT NULL UNIQUE,
  github_url TEXT NOT NULL,
  description TEXT,
  momentum_score FLOAT DEFAULT 0,
  last_push TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Activity Log (every GitHub event becomes a row here)
CREATE TABLE activities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, -- 'push', 'merge', 'release', 'pr_opened'
  event_data JSONB NOT NULL, -- raw GitHub webhook data
  created_at TIMESTAMP DEFAULT NOW()
);

-- Wins (merged PRs, releases, milestones)
CREATE TABLE wins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  win_type TEXT, -- 'release', 'milestone', 'feature'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily Focus (what the engine calculated you should do)
CREATE TABLE daily_focus (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL UNIQUE,
  priorities JSONB NOT NULL, -- array of {project_id, task, reason}
  mode TEXT DEFAULT 'normal', -- 'normal', 'low-energy', 'beast'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Content Drafts (AI-generated posts waiting for approval)
CREATE TABLE content_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  activity_id UUID REFERENCES activities(id) ON DELETE SET NULL,
  platform TEXT, -- 'linkedin', 'twitter', 'dev'
  content TEXT NOT NULL,
  status TEXT DEFAULT 'draft', -- 'draft', 'approved', 'published'
  approved_at TIMESTAMP,
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Memory Snapshots (project state over time)
CREATE TABLE memory_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  snapshot_data JSONB NOT NULL, -- {skills_demonstrated, architecture_shifts, etc}
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Output:** Neon database with schema, connection string saved

---

### 0.3 Set Up GitHub App
```bash
# What you're doing:
# - Creating a GitHub App that can listen to your repos
# - This is how the agent gets real-time events

Steps:
1. Go to github.com/settings/developers
2. Click "New GitHub App"
3. Name: "Penjy Agent"
4. Homepage: your Railway project URL (we'll set this up)
5. Webhook URL: https://your-railway-app.up.railway.app/webhooks/github
6. Events to subscribe to:
   ✓ Push
   ✓ Pull request
   ✓ Release
   ✓ Repository
7. Permissions:
   ✓ Read-only access to code, metadata, contents
8. Install app to your account
```

**Output:** GitHub App webhook secret, App ID, Private key (save these)

---

### 0.4 Set Up Telegram Bot
```bash
# What you're doing:
# - Creating the command interface for the system
# - This is where you'll see alerts, approve content, check focus

Steps:
1. Open Telegram
2. Message @BotFather
3. /newbot
   Name: "Penjy Focus"
   Username: something unique like "penjy_focus_bot"
4. Save the token (looks like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
5. Go to https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-railway-app.up.railway.app/webhooks/telegram
```

**Output:** Telegram bot token, bot username

---

## PHASE 1: The Brain (Days 3-5)
**Goal:** Build the agent that makes decisions and stores everything in Neon.

### 1.1 Create the Railway Backend (Node.js + FastAPI reference)

I'm showing **Node.js (Fastify)** because it's faster to deploy on Railway and lighter on resources.

**Project Structure:**
```
penjy-agent/
├── src/
│   ├── index.js (main entry point)
│   ├── webhooks/
│   │   ├── github.js (process GitHub events)
│   │   └── telegram.js (handle Telegram commands)
│   ├── agents/
│   │   ├── focus-engine.js (calculate daily priorities)
│   │   ├── content-engine.js (generate posts)
│   │   └── momentum-calculator.js (score projects)
│   ├── db/
│   │   └── client.js (Neon connection)
│   └── utils/
│       └── telegram-client.js (send messages)
├── .env.example
└── package.json
```

**Step 1: Create package.json**
```json
{
  "name": "penjy-agent",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "node src/index.js",
    "start": "node src/index.js"
  },
  "dependencies": {
    "fastify": "^4.24.3",
    "pg": "^8.11.3",
    "@anthropic-ai/sdk": "^0.15.1",
    "axios": "^1.6.2",
    "dotenv": "^16.3.1"
  }
}
```

**Step 2: Create src/db/client.js**
```javascript
import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
});

export async function query(text, params) {
  const client = await pool.connect();
  try {
    return await client.query(text, params);
  } finally {
    client.release();
  }
}

export default pool;
```

**Step 3: Create src/agents/momentum-calculator.js**
```javascript
// Momentum = how fast your project is moving + how close to revenue

export function calculateMomentumScore(activities, wins, lastPush) {
  const now = new Date();
  const daysSinceLastPush = (now - new Date(lastPush)) / (1000 * 60 * 60 * 24);
  
  // Decay factor: projects inactive for >7 days get penalized
  const decayFactor = daysSinceLastPush > 7 ? 0.3 : 1.0;
  
  // Base score from activity frequency
  const activityScore = activities.length * 10;
  
  // Bonus for releases (major wins)
  const releaseBonus = wins.filter(w => w.win_type === 'release').length * 50;
  
  // Final momentum
  const momentum = (activityScore + releaseBonus) * decayFactor;
  
  return {
    score: Math.min(momentum, 100), // cap at 100
    isInactive: daysSinceLastPush > 7,
    lastActivityDays: Math.round(daysSinceLastPush),
  };
}

export function shouldShipOrKill(momentumScore, revenueProximity) {
  // If momentum < 20 and revenue proximity < 0.5, it's a "Kill" candidate
  return {
    shouldShip: momentumScore > 60 || revenueProximity > 0.8,
    shouldKill: momentumScore < 20 && revenueProximity < 0.5,
    shouldMaintain: momentumScore >= 20 && revenueProximity < 0.5,
  };
}
```

**Step 4: Create src/agents/focus-engine.js**
```javascript
import { query } from '../db/client.js';
import { calculateMomentumScore } from './momentum-calculator.js';

export async function calculateDailyFocus(mode = 'normal') {
  // Step 1: Get all projects with recent activity
  const projectsResult = await query(`
    SELECT 
      p.id,
      p.repo_name,
      p.momentum_score,
      COUNT(a.id) as recent_activities
    FROM projects p
    LEFT JOIN activities a ON p.id = a.project_id 
      AND a.created_at > NOW() - INTERVAL '7 days'
    GROUP BY p.id
    ORDER BY p.momentum_score DESC
    LIMIT 10
  `);

  // Step 2: For each project, recalculate momentum
  const projectsWithScore = await Promise.all(
    projectsResult.rows.map(async (project) => {
      const activitiesResult = await query(
        'SELECT * FROM activities WHERE project_id = $1 AND created_at > NOW() - INTERVAL \'7 days\'',
        [project.id]
      );
      
      const winsResult = await query(
        'SELECT * FROM wins WHERE project_id = $1 AND created_at > NOW() - INTERVAL \'30 days\'',
        [project.id]
      );

      const { score, isInactive } = calculateMomentumScore(
        activitiesResult.rows,
        winsResult.rows,
        project.last_push
      );

      return {
        projectId: project.id,
        repoName: project.repo_name,
        momentumScore: score,
        isInactive,
        activities: activitiesResult.rows.length,
      };
    })
  );

  // Step 3: Rank and select top 3 based on mode
  let topProjects = projectsWithScore.sort((a, b) => b.momentumScore - a.momentumScore);

  if (mode === 'low-energy') {
    // Pick easier, high-impact maintenance tasks
    topProjects = topProjects.filter(p => !p.isInactive).slice(0, 3);
  } else if (mode === 'beast') {
    // Pick most momentum-heavy projects (deep work on what's moving)
    topProjects = topProjects.slice(0, 3);
  } else {
    // Normal: balanced mix
    topProjects = topProjects.slice(0, 3);
  }

  // Step 4: Store in database
  const prioritiesJson = topProjects.map(p => ({
    projectId: p.projectId,
    repo: p.repoName,
    momentum: p.momentumScore,
    reason: p.momentumScore > 70 ? 'High momentum - push for release' 
            : p.activities > 5 ? 'Recent activity - capitalize'
            : 'Needs attention - low momentum'
  }));

  await query(
    `INSERT INTO daily_focus (date, priorities, mode) 
     VALUES (CURRENT_DATE, $1, $2)
     ON CONFLICT (date) DO UPDATE SET 
       priorities = $1, mode = $2`,
    [JSON.stringify(prioritiesJson), mode]
  );

  return prioritiesJson;
}
```

**Step 5: Create src/webhooks/github.js**
```javascript
import { query } from '../db/client.js';
import crypto from 'crypto';

// Verify GitHub webhook signature
export function verifyGitHubSignature(req, secret) {
  const signature = req.headers['x-hub-signature-256'];
  const payload = req.rawBody; // you need to capture raw body
  
  const hash = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(`sha256=${hash}`),
    Buffer.from(signature)
  );
}

export async function handleGitHubEvent(event, action, payload) {
  const { repository, pusher, pull_request, release } = payload;
  
  // Step 1: Ensure project exists
  const projectCheck = await query(
    'SELECT id FROM projects WHERE repo_name = $1',
    [repository.name]
  );

  let projectId;
  if (projectCheck.rows.length === 0) {
    // Auto-create project
    const insertResult = await query(
      `INSERT INTO projects (repo_name, github_url, description, last_push)
       VALUES ($1, $2, $3, NOW())
       RETURNING id`,
      [repository.name, repository.html_url, repository.description]
    );
    projectId = insertResult.rows[0].id;
  } else {
    projectId = projectCheck.rows[0].id;
  }

  // Step 2: Create activity log entry
  const eventType = event === 'pull_request' ? 'merge' : event;
  
  await query(
    `INSERT INTO activities (project_id, event_type, event_data)
     VALUES ($1, $2, $3)`,
    [projectId, eventType, JSON.stringify(payload)]
  );

  // Step 3: If it's a release or merge, create a "win"
  if (event === 'release' || (event === 'pull_request' && action === 'closed' && pull_request.merged)) {
    await query(
      `INSERT INTO wins (project_id, title, win_type)
       VALUES ($1, $2, $3)`,
      [projectId, event === 'release' ? release.name : pull_request.title, event]
    );
  }

  // Step 4: Update project momentum
  const activitiesResult = await query(
    'SELECT * FROM activities WHERE project_id = $1 AND created_at > NOW() - INTERVAL \'7 days\'',
    [projectId]
  );

  const momentumScore = Math.min(activitiesResult.rows.length * 15, 100);

  await query(
    'UPDATE projects SET momentum_score = $1, last_push = NOW() WHERE id = $2',
    [momentumScore, projectId]
  );

  return { projectId, eventType };
}
```

**Step 6: Create src/index.js (Main server)**
```javascript
import Fastify from 'fastify';
import { handleGitHubEvent, verifyGitHubSignature } from './webhooks/github.js';
import { handleTelegramCommand } from './webhooks/telegram.js';
import { calculateDailyFocus } from './agents/focus-engine.js';

const app = Fastify({ logger: true });

// Store raw body for GitHub signature verification
app.addHook('preHandler', async (request, reply) => {
  request.rawBody = await request.getRawBody();
});

// ====== WEBHOOKS ======

// GitHub webhook
app.post('/webhooks/github', async (request, reply) => {
  try {
    const signature = request.headers['x-hub-signature-256'];
    if (!signature) {
      return reply.status(401).send({ error: 'Unauthorized' });
    }

    // Verify signature
    verifyGitHubSignature(request, process.env.GITHUB_WEBHOOK_SECRET);

    const event = request.headers['x-github-event'];
    const action = request.body.action;

    const result = await handleGitHubEvent(event, action, request.body);

    console.log(`✓ GitHub event processed: ${event} on ${result.projectId}`);
    
    return reply.send({ status: 'processed', ...result });
  } catch (error) {
    console.error('GitHub webhook error:', error);
    return reply.status(500).send({ error: error.message });
  }
});

// Telegram webhook
app.post('/webhooks/telegram', async (request, reply) => {
  try {
    const message = request.body.message;
    if (!message) return reply.send({ ok: true });

    const result = await handleTelegramCommand(message);
    return reply.send({ ok: true, result });
  } catch (error) {
    console.error('Telegram webhook error:', error);
    return reply.send({ ok: true }); // Always return ok to Telegram
  }
});

// ====== PUBLIC ENDPOINTS (for Portfolio) ======

app.get('/public/projects', async (request, reply) => {
  const result = await query('SELECT * FROM projects ORDER BY momentum_score DESC');
  return result.rows;
});

app.get('/public/wins', async (request, reply) => {
  const result = await query(
    'SELECT w.*, p.repo_name FROM wins w JOIN projects p ON w.project_id = p.id ORDER BY w.created_at DESC LIMIT 20'
  );
  return result.rows;
});

app.get('/public/activity', async (request, reply) => {
  const result = await query(
    'SELECT a.*, p.repo_name FROM activities a JOIN projects p ON a.project_id = p.id ORDER BY a.created_at DESC LIMIT 50'
  );
  return result.rows;
});

app.get('/public/focus', async (request, reply) => {
  const result = await query(
    'SELECT * FROM daily_focus WHERE date = CURRENT_DATE'
  );
  return result.rows[0] || { priorities: [] };
});

// ====== HEALTH CHECK ======

app.get('/health', async (request, reply) => {
  return { status: 'ok', timestamp: new Date().toISOString() };
});

// ====== START SERVER ======

const PORT = process.env.PORT || 3000;
app.listen({ port: PORT, host: '0.0.0.0' }, (err, address) => {
  if (err) {
    console.error(err);
    process.exit(1);
  }
  console.log(`Server running at ${address}`);
});
```

**Step 7: Create src/webhooks/telegram.js**
```javascript
import axios from 'axios';
import { query } from '../db/client.js';
import { calculateDailyFocus } from '../agents/focus-engine.js';

const TELEGRAM_API = `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}`;

export async function sendTelegramMessage(chatId, text, options = {}) {
  return axios.post(`${TELEGRAM_API}/sendMessage`, {
    chat_id: chatId,
    text,
    parse_mode: 'HTML',
    ...options,
  });
}

export async function handleTelegramCommand(message) {
  const chatId = message.chat.id;
  const text = message.text || '';
  const command = text.split(' ')[0];

  try {
    switch (command) {
      case '/focus':
        const focus = await calculateDailyFocus('normal');
        const focusText = focus
          .map((p, i) => `<b>${i + 1}. ${p.repo}</b>\n📊 Momentum: ${p.momentum}\n💡 ${p.reason}`)
          .join('\n\n');
        
        await sendTelegramMessage(chatId, `🎯 <b>Today's Focus</b>\n\n${focusText}`);
        break;

      case '/wins':
        const winsResult = await query(
          'SELECT w.title, w.created_at, p.repo_name FROM wins w JOIN projects p ON w.project_id = p.id ORDER BY w.created_at DESC LIMIT 5'
        );
        const winsText = winsResult.rows
          .map(w => `✅ <b>${w.title}</b> (${w.repo_name})`)
          .join('\n');
        
        await sendTelegramMessage(chatId, `🏆 <b>Recent Wins</b>\n\n${winsText}`);
        break;

      case '/done':
        const taskName = text.replace('/done ', '').trim();
        await sendTelegramMessage(chatId, `✅ Logged: "${taskName}"\n\n(This would update memory and trigger content drafts)`);
        break;

      case '/ghost':
        const ghostResult = await query(
          'SELECT repo_name, momentum_score FROM projects WHERE last_push < NOW() - INTERVAL \'7 days\' ORDER BY momentum_score DESC'
        );
        const ghostText = ghostResult.rows
          .map(p => `👻 <b>${p.repo_name}</b> (${Math.round(p.momentum_score)} momentum)`)
          .join('\n');
        
        await sendTelegramMessage(chatId, `<b>Inactive Projects</b>\n\n${ghostText || 'All projects active!'}`);
        break;

      default:
        await sendTelegramMessage(chatId, `Unknown command. Available:\n/focus\n/wins\n/ghost\n/done [task]`);
    }
  } catch (error) {
    console.error('Telegram command error:', error);
    await sendTelegramMessage(chatId, '❌ Error processing command');
  }
}
```

**Step 8: Create .env.example**
```env
# Database
DATABASE_URL=postgresql://user:password@host/dbname

# GitHub
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Server
PORT=3000
NODE_ENV=production
```

---

### 1.2 Deploy to Railway

```bash
# In your repo
git add .
git commit -m "feat: Initial agent backend"
git push

# In Railway dashboard:
# 1. Connect your GitHub repo
# 2. Add environment variables from .env
# 3. Set start command: npm start
# 4. Deploy

# Once deployed, grab your Railway URL:
# https://your-project-xxx.up.railway.app
```

**Output:** Running agent backend with GitHub webhooks working

---

## PHASE 2: The Nervous System (Days 6-7)
**Goal:** n8n workflows that connect the dots without touching agent logic.

### 2.1 Self-host n8n on Railway

```bash
# Create new Railway service for n8n
# Use template: https://railway.app/template/n8n

# Or docker image: n8nio/n8n

# Once running:
# 1. Go to n8n dashboard
# 2. Set up authentication
# 3. Configure webhook URLs
```

### 2.2 Build 3 Workflows

**Workflow 1: GitHub → Agent**
```
Trigger: GitHub webhook (any push/PR/release)
  ↓
HTTP Request: POST /webhooks/github (to your Railway agent)
  ↓
Wait for response
  ↓
Log result
```

**Workflow 2: Content Approval Loop**
```
Trigger: Database polling (check for content_drafts with status='draft')
  ↓
Send Telegram: "New post for approval"
  ↓
Wait for user approval (via inline button)
  ↓
IF approved:
  → Update draft status to 'approved'
  → Send to Buffer (scheduling)
  → Update status to 'published'
```

**Workflow 3: Daily Focus Broadcast**
```
Trigger: Cron (daily at 7 AM)
  ↓
HTTP Request: GET /public/focus (from your agent)
  ↓
Format response
  ↓
Send to Telegram
```

**Output:** n8n workflows running, integrations live

---

## PHASE 3: The Face (Days 8-10)
**Goal:** Portfolio reads from your agent API.

### 3.1 Create Portfolio (Next.js)

```bash
npx create-next-app@latest penjy-portfolio --typescript
cd penjy-portfolio
```

**Key files:**

`lib/api.ts`:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_URL;

export async function getProjects() {
  const res = await fetch(`${API_BASE}/public/projects`, { next: { revalidate: 60 } });
  return res.json();
}

export async function getWins() {
  const res = await fetch(`${API_BASE}/public/wins`, { next: { revalidate: 60 } });
  return res.json();
}

export async function getActivity() {
  const res = await fetch(`${API_BASE}/public/activity`, { next: { revalidate: 60 } });
  return res.json();
}

export async function getTodaysFocus() {
  const res = await fetch(`${API_BASE}/public/focus`, { next: { revalidate: 300 } });
  return res.json();
}
```

`app/page.tsx`:
```typescript
import { getProjects, getWins, getTodaysFocus } from '@/lib/api';

export default async function Home() {
  const [projects, wins, focus] = await Promise.all([
    getProjects(),
    getWins(),
    getTodaysFocus(),
  ]);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Building Live</h1>

      {/* Today's Focus */}
      {focus?.priorities && (
        <section className="mb-12 p-6 bg-slate-900 rounded-lg">
          <h2 className="text-2xl font-bold mb-4">🎯 Today's Focus</h2>
          {focus.priorities.map((p, i) => (
            <div key={i} className="mb-3">
              <p className="font-semibold">{p.repo}</p>
              <p className="text-sm text-gray-300">{p.reason}</p>
            </div>
          ))}
        </section>
      )}

      {/* Recent Wins */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-4">✅ Recent Wins</h2>
        {wins.slice(0, 5).map(win => (
          <div key={win.id} className="p-4 bg-slate-800 rounded mb-3">
            <p className="font-semibold">{win.title}</p>
            <p className="text-sm text-gray-400">{win.repo_name}</p>
          </div>
        ))}
      </section>

      {/* Active Projects */}
      <section>
        <h2 className="text-2xl font-bold mb-4">🚀 Projects</h2>
        {projects.slice(0, 10).map(project => (
          <div key={project.id} className="p-4 bg-slate-800 rounded mb-3 flex justify-between items-center">
            <div>
              <p className="font-semibold">{project.repo_name}</p>
              <p className="text-sm text-gray-400">{project.description}</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold">{Math.round(project.momentum_score)}</p>
              <p className="text-xs text-gray-400">momentum</p>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
```

`.env.local`:
```env
NEXT_PUBLIC_AGENT_API_URL=https://your-railway-agent.up.railway.app
```

### 3.2 Deploy Portfolio to Vercel

```bash
# Push to GitHub
git add .
git commit -m "feat: Live portfolio"
git push

# In Vercel:
# 1. Connect repo
# 2. Add environment variables
# 3. Deploy
```

**Output:** Live portfolio at yourname.vercel.app, pulling live data

---

## PHASE 4: Wire It All (Days 11-14)
**Goal:** Full loop: GitHub → Agent → n8n → Content → Telegram → Buffer → Portfolio

### 4.1 Content Generation Engine

Add to `src/agents/content-engine.js`:

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

export async function generateContentDraft(activity, project) {
  // activity = {event_type, event_data, ...}
  // project = {repo_name, momentum_score, ...}

  const prompt = `
You are a technical marketing expert. Convert this GitHub activity into 2-3 short, authentic LinkedIn posts.

Activity: ${activity.event_type} on ${project.repo_name}
Details: ${JSON.stringify(activity.event_data, null, 2)}

Rules:
- Focus on WHAT was built, not motivation
- Use specific technical details (library names, patterns, etc)
- Include a call-to-action (try it, feedback, etc)
- Keep it under 200 characters per post
- Make it sound authentic (not AI)

Return ONLY a JSON array of posts:
[
  { "platform": "linkedin", "content": "..." },
  { "platform": "twitter", "content": "..." }
]
`;

  const response = await client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    messages: [
      { role: 'user', content: prompt }
    ],
  });

  const text = response.content[0].type === 'text' ? response.content[0].text : '';
  
  // Parse JSON from response
  const jsonMatch = text.match(/\[[\s\S]*\]/);
  if (!jsonMatch) {
    console.error('No JSON found in response:', text);
    return [];
  }

  return JSON.parse(jsonMatch[0]);
}

export async function createDraftsFromActivity(activityId, projectId) {
  const activityResult = await query('SELECT * FROM activities WHERE id = $1', [activityId]);
  const projectResult = await query('SELECT * FROM projects WHERE id = $1', [projectId]);

  if (!activityResult.rows.length || !projectResult.rows.length) return [];

  const activity = activityResult.rows[0];
  const project = projectResult.rows[0];

  const drafts = await generateContentDraft(activity, project);

  // Save drafts to DB
  for (const draft of drafts) {
    await query(
      `INSERT INTO content_drafts (activity_id, platform, content, status)
       VALUES ($1, $2, $3, 'draft')`,
      [activityId, draft.platform, draft.content]
    );
  }

  return drafts;
}
```

Update GitHub webhook to trigger content generation:

```javascript
// In handleGitHubEvent, after creating activity:

if (eventType === 'release' || eventType === 'merge') {
  // Trigger content generation
  await createDraftsFromActivity(/* ... */);
  // n8n will pick up new drafts and send for approval
}
```

### 4.2 Test the Full Loop

```bash
# 1. Make a push to one of your repos
# 2. Watch GitHub webhook hit your agent
# 3. Check Neon DB for new activity
# 4. Check n8n for content draft (via polling)
# 5. Approve in Telegram
# 6. Check Buffer for scheduled post
# 7. Refresh portfolio.vercel.app → see new activity
```

**Output:** Fully functional loop

---

## Implementation Timeline Summary

| Phase | Days | Deliverable |
|-------|------|-------------|
| 0: Setup | 1-2 | Railway project, Neon DB, GitHub App, Telegram Bot |
| 1: Brain | 3-5 | Working agent backend, all endpoints live, Telegram commands responding |
| 2: Nerves | 6-7 | n8n workflows, content pipeline operational |
| 3: Face | 8-10 | Portfolio live, pulling real data from agent API |
| 4: Wire | 11-14 | Full end-to-end: push code → portfolio updates automatically |

---

## What NOT to Do (Anti-Patterns)

❌ Don't build the portfolio first  
❌ Don't put logic in n8n  
❌ Don't let portfolio write back to agent  
❌ Don't try to be perfect before shipping  
❌ Don't over-engineer workflows (3 max initially)  

---

## Minimal Success Criteria (Day 5)

By end of Phase 1, you should have:
- ✅ Agent running on Railway
- ✅ GitHub webhook firing and creating DB entries
- ✅ Telegram commands responding
- ✅ `/focus` shows top 3 projects
- ✅ Data flowing: GitHub → Neon

If you have this, **everything else is additive**. You're already winning.

---

## Quick Commands Reference

```bash
# Deploy agent
git push  # Railway auto-deploys

# Check logs
railway logs

# View Neon data
SELECT * FROM projects;
SELECT * FROM activities ORDER BY created_at DESC;

# Test Telegram
/focus
/wins
/ghost

# Test endpoints
curl https://your-agent.up.railway.app/public/projects
curl https://your-agent.up.railway.app/public/focus
```

---

## Questions to Answer Before You Start

1. **Which GitHub repos should the agent watch?** (Add them to GitHub App installation)
2. **What's your Telegram username?** (For bot approval messages)
3. **Do you have Anthropic API key?** (For content generation)
4. **Buffer account?** (For social scheduling, optional for Phase 1)

Once you answer these, you're ready to start Phase 0.