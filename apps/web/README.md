# Woflo Dispatcher Dashboard

Next.js-based web application for dispatchers to manage diesel shop scheduling and operations.

## Features

- 📅 **Schedule Board**: View and manage technician schedules
- 📋 **Work Order Queue**: Manage work orders and priorities
- ✅ **Task Management**: View and update task assignments
- 🔄 **Real-time Updates**: React Query for data synchronization
- 🎨 **Modern UI**: Tailwind CSS styling
- 🔐 **Authentication**: Supabase Auth integration

## Prerequisites

- Node.js 18+ and npm
- Running Woflo API (apps/api)
- Supabase project (optional, for auth)

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
apps/web/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── globals.css   # Global styles
│   ├── lib/              # Utilities
│   │   └── api.ts        # API client
│   └── components/       # React components (to be added)
├── public/               # Static assets
├── package.json
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## API Integration

The app connects to the Woflo FastAPI backend:

- **Schedules**: `/v1/schedules`
- **Work Orders**: `/v1/work-orders`
- **Tasks**: `/v1/tasks`
- **Jobs**: `/v1/jobs`

See `src/lib/api.ts` for the complete API client.

## Development

### Build for Production

```bash
npm run build
```

### Run Production Server

```bash
npm start
```

### Linting

```bash
npm run lint
```

## Key Technologies

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS
- **@dnd-kit**: Drag-and-drop functionality (planned)
- **@tanstack/react-query**: Data fetching and caching (planned)
- **@supabase/supabase-js**: Authentication (planned)

## Next Steps

To complete the dashboard, implement:

1. **Schedule Board Component**
   - Calendar/timeline view
   - Drag-and-drop task assignment
   - Tech availability visualization

2. **Work Order Queue**
   - Filterable list
   - Priority sorting
   - Quick actions

3. **Authentication**
   - Supabase Auth provider
   - Protected routes
   - Role-based access

4. **Real-time Features**
   - React Query for polling
   - Optimistic updates
   - WebSocket support (future)

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Configure environment variables
4. Deploy

### Other Platforms

- Railway
- Netlify
- AWS Amplify

## Related Documentation

- [Job Queue System](../../docs/job_queue.md)
- [Scheduler Documentation](../../docs/scheduler.md)
- [API Documentation](http://localhost:8000/docs)

## License

Part of the Woflo monorepo project.
