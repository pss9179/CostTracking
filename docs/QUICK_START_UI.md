# LLM Observe - Quick Start Guide

## 🚀 Getting Started

### 1. Start the Backend
```bash
# Terminal 1
cd /Users/pranavsrigiriraju/CostTracking
make dev-api
```

The collector API will start on `http://localhost:8000`

### 2. Start the Frontend
```bash
# Terminal 2
cd /Users/pranavsrigiriraju/CostTracking
make dev-web
```

The dashboard will be available at `http://localhost:3000`

### 3. Generate Test Data
```bash
# Terminal 3
cd /Users/pranavsrigiriraju/CostTracking
make seed
```

This will create sample runs with hierarchical traces.

## 📱 Navigation

The app has a persistent top navigation bar:

- **Overview** (`/`) - Dashboard with KPIs, trends, and recent runs
- **Runs** (`/runs`) - Searchable, sortable list of all runs
- **Costs** (`/costs`) - Detailed cost analysis by provider/model/section
- **Insights** (`/insights`) - Automated alerts and anomaly detection

## 🎯 Key Features to Try

### Dashboard (`/`)
1. Check the **KPI cards** at the top - notice the trend indicators
2. Scroll to **Cost Trend Chart** - see 7-day history by provider
3. View **Top Sections** table - identify expensive sections
4. Check **Provider Breakdown** with progress bars

### Runs Page (`/runs`)
1. Use the **search bar** to filter runs (try typing a section name)
2. **Click column headers** to sort (try "Cost" descending)
3. **Export CSV** button downloads filtered results
4. **Click any row** to view details

### Run Detail Page (`/runs/[runId]`)
1. Start with **Hierarchical Trace** tab - see nested structure
2. Switch to **Waterfall Timeline** - visualize timing and sequence
3. Try **Flat Event List** - traditional table view
4. Check breakdown tabs - by Section, Provider, Model

### Costs Page (`/costs`)
1. **By Provider** tab - see pie chart distribution
2. **By Model** tab - identify expensive models, bar chart
3. **By Section Path** tab - hierarchical cost attribution
4. Use **Export** buttons for data analysis

### Insights Page (`/insights`)
1. View **summary cards** - total alerts by type
2. **Click category headers** to expand/collapse
3. Check specific alerts for **cost spikes** or **inefficiencies**
4. **Click links** to jump to relevant runs

## 🔍 Search & Filter

### Time Ranges
All pages support time range filtering:
- Presets: **1h**, **24h**, **7d**, **30d**, **90d**
- Custom: Click **Custom** button, pick start/end dates

### Search
- Runs page: Search by run ID, section name
- Filters persist in URL - share links with teammates!

### Sort
Click any column header with an up/down arrow icon:
- First click: Descending
- Second click: Ascending
- Third click: Back to default

## 💡 Pro Tips

### Finding Cost Issues
```
1. Dashboard → Notice cost spike
2. Insights → See "Section Spike" alert
3. Click alert → View related runs
4. Click run → Waterfall view
5. Identify slow/expensive call
```

### Comparing Models
```
1. Costs → By Model tab
2. Sort by "Cost" column
3. Compare GPT-4o vs GPT-4o-mini costs
4. Check latency differences
5. Decide if cheaper model is viable
```

### Analyzing Agent Performance
```
1. Runs → Search "agent:researcher"
2. Sort by "Cost" descending
3. Click expensive run
4. View Hierarchical Trace
5. See which tools are costly
```

### Exporting Data
```
1. Runs page → Filter/search
2. Click "Export CSV"
3. Open in Excel/Google Sheets
4. Create custom reports
```

## 🎨 UI Conventions

### Color Coding
- **Blue**: OpenAI
- **Purple**: Pinecone
- **Orange**: Anthropic
- **Green**: Success/OK status
- **Red**: Error/Alert

### Badge Types
- **Secondary** (gray): Sections, general labels
- **Outline**: Models, endpoints
- **Default** (blue): OK status
- **Destructive** (red): Error status

### Icons
- 💰 **DollarSign**: Cost-related
- 📊 **TrendingUp**: Performance/trends
- ⚡ **Activity**: API calls
- 🔔 **Bell**: Alerts/insights
- 📋 **List**: Runs/events
- ⏱️ **Clock**: Latency/timing

## ⚡ Performance

### Virtualized Lists
The Runs page uses virtualization:
- Only renders visible rows
- Handles 1000s of runs smoothly
- Scroll is buttery smooth
- Search/sort happens instantly

### Debounced Search
Search has 300ms debounce:
- Type freely
- Filtering happens after you pause
- No laggy typing experience

### Efficient Aggregations
- Data processed client-side
- Memoized with `useMemo`
- Re-calculates only when needed

## 🐛 Troubleshooting

### "No runs found"
```bash
# Generate test data
make seed
```

### Waterfall shows nothing
- Check that events have `created_at` timestamps
- Ensure events are sorted by time
- Verify `latency_ms` is present

### Charts not showing
- Check browser console for errors
- Ensure data format matches expected shape
- Try refreshing the page

### Navigation not appearing
- Check that `<Navigation />` is in `app/layout.tsx`
- Verify imports are correct
- Clear browser cache

## 📊 Data Flow

```
SDK (Python) → Patches OpenAI/Pinecone
       ↓
    Events emitted with span_id, parent_span_id, section_path
       ↓
Collector API → Stores in SQLite
       ↓
Dashboard → Fetches via /api routes
       ↓
Components → Aggregate, visualize, export
```

## 🎓 Learn More

- **Hierarchical Tracing**: See `docs/semantic_sections.md`
- **API Endpoints**: See main `README.md`
- **UI Architecture**: See `docs/UI_OVERHAUL_SUMMARY.md`

## ✅ Checklist for First Use

- [ ] Backend running on `:8000`
- [ ] Frontend running on `:3000`
- [ ] Test data generated with `make seed`
- [ ] Visited Dashboard - see KPIs
- [ ] Viewed Runs page - tried search/sort
- [ ] Opened a Run Detail - checked all 3 tabs
- [ ] Explored Costs page - viewed all tabs
- [ ] Checked Insights page - expanded alerts
- [ ] Exported CSV from Runs page
- [ ] Shared a filtered URL with yourself

## 🎉 You're Ready!

You now have a **production-ready LLM cost observability dashboard** with:
- ✅ Real-time monitoring
- ✅ Hierarchical trace visualization
- ✅ Automated insights
- ✅ Cost analysis tools
- ✅ Export capabilities

Happy observing! 🚀

