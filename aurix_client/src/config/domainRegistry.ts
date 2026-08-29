import React from 'react';
import {
  LayoutDashboard, Target, TestTube, Bot, Truck, Boxes, Factory, ShoppingCart, Share2,
  TrendingUp, Landmark, ShieldAlert, GitFork, Database, Sliders, Activity, BarChart3,
  LineChart, Layers, Gauge, Workflow, ShieldCheck, PieChart, FileText, Zap,
  AlertTriangle, Scale, Network, Clock, PackageCheck, Shield, Terminal
} from 'lucide-react';
import { SubdomainItem } from '@/components/navigation/SubdomainWorkspaceSelector';
import { DomainKpi } from '@/components/domain/DomainLandingHero';
import { DomainSignal } from '@/components/domain/DomainSignalsOverview';

export interface DomainDefinition {
  domainTag: string;
  id: string;
  title: string;
  description: string;
  route: string;
  icon: React.ComponentType<{ className?: string }>;
  telemetryStream: string;
  status: 'OPTIMAL' | 'DEGRADED' | 'WATCH' | 'CRITICAL';
  kpis: DomainKpi[];
  signals: DomainSignal[];
  subdomains: SubdomainItem[];
}

export const DOMAIN_REGISTRY: Record<string, DomainDefinition> = {
  'overview': {
    domainTag: '01',
    id: 'overview',
    title: 'Executive Command & Overview',
    description: 'Autonomous enterprise control tower delivering real-time operational posture, macro financial rollups, and cross-domain anomaly telemetry.',
    route: '/',
    icon: LayoutDashboard,
    telemetryStream: 'CROSS-DOMAIN AGGREGATOR',
    status: 'OPTIMAL',
    kpis: [
      { label: 'ENTERPRISE HEALTH', value: '98.4%', delta: '+1.2%', deltaType: 'positive', provenance: 'SYSTEM_AUDIT' },
      { label: 'WORKING CAPITAL', value: '$14.5M', delta: '-3.1%', deltaType: 'positive', provenance: 'FINANCE_ENGINE' },
      { label: 'ACTIVE DISRUPTIONS', value: '02', delta: '-1', deltaType: 'positive', provenance: 'RISK_RADAR' },
      { label: 'PRESCRIPTIVE SAVINGS', value: '$420K', delta: '+18.4%', deltaType: 'positive', provenance: 'DECISION_ENGINE' },
    ],
    signals: [
      { id: 'sig-01', title: 'Tier-1 Supplier Lead Time Variance', impact: '$120K at risk', type: 'risk', severity: 'warning', actionPrompt: 'Inspect Supply Chain' },
      { id: 'sig-02', title: 'Dynamic Multi-Echelon Rebalance', impact: '+$84K Working Capital', type: 'opportunity', severity: 'info', actionPrompt: 'Review Prescriptions' },
    ],
    subdomains: [
      { id: 'summary', title: 'Executive Briefing', description: 'Cross-functional macro overview, revenue posture, and business health scorecards.', icon: LayoutDashboard, metric: '98.4%', metricLabel: 'HEALTH SCORE', badge: 'EXECUTIVE' },
      { id: 'telemetry', title: 'System Telemetry', description: 'Live database transaction volume, API latency percentiles, and Celery task execution queues.', icon: Activity, metric: '14ms', metricLabel: 'P99 LATENCY', badge: 'LIVE FEED' },
    ]
  },
  'supply-chain': {
    domainTag: '02',
    id: 'supply-chain',
    title: 'Supply Chain Intelligence',
    description: 'Demand forecasting with ADI/CV² classification, multi-echelon capacity planning, automated replenishment solvers, and network risk propagation.',
    route: '/supply-chain',
    icon: Truck,
    telemetryStream: 'MRP & FORECAST ENGINE',
    status: 'OPTIMAL',
    kpis: [
      { label: 'FORECAST ACCURACY', value: '94.2%', delta: '+2.8%', deltaType: 'positive', provenance: 'FORECAST_ENGINE' },
      { label: 'WEIGHTED BIAS', value: '-0.8%', delta: 'Optimal', deltaType: 'neutral', provenance: 'ML_RETRAIN_V2' },
      { label: 'FILL RATE (OTIF)', value: '96.8%', delta: '+0.5%', deltaType: 'positive', provenance: 'COMMERCIAL_API' },
      { label: 'REPLENISHMENT ORDERS', value: '38 POs', delta: 'Pending Gate', deltaType: 'neutral', provenance: 'ACTION_CENTER' },
    ],
    signals: [
      { id: 'sc-sig-1', title: 'Lumpy Demand Pattern Detected (SKU-001)', impact: 'ADI: 1.48 | CV²: 0.62', type: 'alert', severity: 'warning', actionPrompt: 'View Croston Model' },
      { id: 'sc-sig-2', title: 'Upstream Fabric Mill Bottleneck', impact: '6-day delay risk', type: 'risk', severity: 'critical', actionPrompt: 'Trigger Countermeasure' },
    ],
    subdomains: [
      { id: 'demand-forecast', title: 'Demand & Forecast', description: 'Croston & Syntetos-Boylan intermittency solvers with confidence cones and forecast accuracy.', icon: LineChart, metric: '94.2%', metricLabel: 'ACCURACY', badge: 'ML ACTIVE' },
      { id: 'planning', title: 'Supply & Capacity Planning', description: 'Constrained multi-tier capacity balancing, machine allocation, and lead time buffers.', icon: Layers, metric: '87.4%', metricLabel: 'CAPACITY UTIL' },
      { id: 'replenishment', title: 'Replenishment Solver', description: 'Dynamic (s, S) and (R, s, S) stochastic replenishment solvers with safety stock buffers.', icon: PackageCheck, metric: '38 POs', metricLabel: 'RECOMMENDED' },
      { id: 'network', title: 'Multi-Echelon Network', description: 'Interactive supply network topology with flow routing and single-source node risks.', icon: Network, metric: '14 Nodes', metricLabel: 'TOPOLOGY' },
    ]
  },
  'inventory': {
    domainTag: '03',
    id: 'inventory',
    title: 'Inventory Optimization & Policies',
    description: 'Dynamic safety stock policies, inventory aging brackets, capital drag decomposition, and real-time stockout risk surfaces.',
    route: '/inventory',
    icon: Boxes,
    telemetryStream: 'STOCK POSITION SENSOR',
    status: 'WATCH',
    kpis: [
      { label: 'TOTAL INVENTORY VALUATION', value: '$8.42M', delta: '-$340K', deltaType: 'positive', provenance: 'BALANCE_SHEET' },
      { label: 'EXCESS CAPITAL LOCKED', value: '$1.12M', delta: 'Down 4.2%', deltaType: 'positive', provenance: 'INVENTORY_AGE' },
      { label: 'STOCKOUT PROBABILITY', value: '1.4%', delta: '-0.3%', deltaType: 'positive', provenance: 'MONTE_CARLO' },
      { label: 'INVENTORY TURNS (DIO)', value: '42 Days', delta: '-4 Days', deltaType: 'positive', provenance: 'FINANCE_ENGINE' },
    ],
    signals: [
      { id: 'inv-sig-1', title: 'Safety Stock Deficit on Fast Movers', impact: '3 SKUs Below ROP', type: 'risk', severity: 'warning', actionPrompt: 'Generate Expedited PO' },
    ],
    subdomains: [
      { id: 'health', title: 'Stock Health & Positioning', description: 'Stock positioning against safety stock and reorder points with stockout risk heatmaps.', icon: Gauge, metric: '98.6%', metricLabel: 'SERVICE LEVEL', badge: 'REAL-TIME' },
      { id: 'policies', title: 'Policy Optimizer', description: 'Service level target simulations vs. working capital cost tradeoffs.', icon: Scale, metric: '99.0%', metricLabel: 'TARGET SL' },
      { id: 'capital', title: 'Holding Capital & Drag', description: 'Decomposition of holding costs, warehouse carry rates, and locked working capital.', icon: Landmark, metric: '$1.12M', metricLabel: 'EXCESS CASH' },
      { id: 'aging', title: 'Inventory Aging & Expiry', description: 'FIFO aging brackets, shelf-life burn-down curves, and deadstock exposure analysis.', icon: Clock, metric: '42 Days', metricLabel: 'AVG DIO' },
    ]
  },
  'sales': {
    domainTag: '04',
    id: 'sales',
    title: 'Commercial Intelligence & Sales',
    description: 'Account 360 customer health matrices, Price-Volume-Mix (PVM) margin waterfalls, fulfillment service levels, and dormancy telemetry.',
    route: '/sales',
    icon: TrendingUp,
    telemetryStream: 'COMMERCIAL DATASTREAM',
    status: 'OPTIMAL',
    kpis: [
      { label: 'BOOKED REVENUE (MTD)', value: '$3.84M', delta: '+12.4%', deltaType: 'positive', provenance: 'SALES_LEDGER' },
      { label: 'AVG GROSS MARGIN', value: '38.4%', delta: '+1.1%', deltaType: 'positive', provenance: 'PVM_ENGINE' },
      { label: 'TIER-A OTIF FULFILLMENT', value: '98.2%', delta: '+0.4%', deltaType: 'positive', provenance: 'LOGISTICS_API' },
      { label: 'DORMANT ACCOUNTS AT RISK', value: '04 Accounts', delta: '$180K Exp', deltaType: 'negative', provenance: 'COMMERCIAL_AI' },
    ],
    signals: [
      { id: 'sls-sig-1', title: 'Key Account Margin Erosion', impact: 'Price Concession: -2.4%', type: 'risk', severity: 'warning', actionPrompt: 'Inspect Account 360' },
    ],
    subdomains: [
      { id: 'accounts', title: 'Account 360 & Health', description: 'Customer concentration, ordering velocity, and account dormancy health scorecards.', icon: PieChart, metric: '92.4', metricLabel: 'HEALTH SCORE', badge: 'HIGH VALUE' },
      { id: 'service', title: 'Service Level & OTIF', description: 'Customer-specific on-time in-full delivery performance and penalty exposure.', icon: PackageCheck, metric: '98.2%', metricLabel: 'OTIF PERFORMANCE' },
      { id: 'pvm', title: 'Price-Volume-Mix Waterfall', description: 'Margin bridge decomposing variance into price realization, unit volume, and mix effects.', icon: BarChart3, metric: '+3.4%', metricLabel: 'NET IMPACT', badge: 'ANALYTICS' },
      { id: 'velocity', title: 'Product Velocity', description: 'Fast vs. slow mover trajectory and cross-sell penetration by region.', icon: Zap, metric: '18 SKUs', metricLabel: 'ACCELERATING' },
    ]
  },
  'finance': {
    domainTag: '05',
    id: 'finance',
    title: 'Financial Economics & Working Capital',
    description: 'Unit economics precision, P&L margin integrity, Gross-to-Net revenue waterfalls, AR/AP aging matrices, and cash conversion cycle models.',
    route: '/finance',
    icon: Landmark,
    telemetryStream: 'FINANCIAL LEDGER SYNC',
    status: 'OPTIMAL',
    kpis: [
      { label: 'NET CONTRIBUTION MARGIN', value: '32.0%', delta: '+1.8%', deltaType: 'positive', provenance: 'ECONOMICS_ENGINE' },
      { label: 'WORKING CAPITAL LOCKED', value: '$1.45M', delta: '-3.2%', deltaType: 'positive', provenance: 'BALANCE_SHEET' },
      { label: 'OVERDUE AR (> 60 DAYS)', value: '$280K', delta: 'Watch Risk', deltaType: 'negative', provenance: 'AR_LEDGER' },
      { label: 'CASH CONVERSION CYCLE', value: '42 Days', delta: '-2 Days', deltaType: 'positive', provenance: 'TREASURY' },
    ],
    signals: [
      { id: 'fin-sig-1', title: 'Apex Global Overdue AR (>74 Days)', impact: '$142,000 High Risk', type: 'risk', severity: 'critical', actionPrompt: 'Open AR Aging Workspace' },
    ],
    subdomains: [
      { id: 'pnl', title: 'P&L & Margin Integrity', description: 'Gross revenue down to net contribution margin decomposition with operational cost tags.', icon: Landmark, metric: '32.0%', metricLabel: 'CONTRIBUTION', badge: 'RECONCILED' },
      { id: 'waterfall', title: 'Gross-to-Net Waterfall', description: 'Discount leakage, rebates, freight deductions, and payment chargeback bridges.', icon: BarChart3, metric: '$412K', metricLabel: 'DEDUCTIONS' },
      { id: 'working-capital', title: 'Working Capital & CCC', description: 'Cash conversion cycle timeline modeling DIO, DSO, and DPO operational velocity.', icon: Clock, metric: '42 Days', metricLabel: 'CCC DURATION' },
      { id: 'aging', title: 'AR/AP Aging & Exposure', description: 'Aging brackets with bad-debt probability models and supplier payable optimization.', icon: Scale, metric: '$280K', metricLabel: 'OVERDUE AR', badge: 'ACTIONABLE' },
    ]
  },
  'manufacturing': {
    domainTag: '06',
    id: 'manufacturing',
    title: 'Manufacturing & Industrial Operations',
    description: 'Work center scheduling, multi-level BOM explosion, capacity bottleneck analysis, Overall Equipment Effectiveness (OEE), and scrap Pareto.',
    route: '/manufacturing',
    icon: Factory,
    telemetryStream: 'MES / SCADA INDUSTRIAL FEED',
    status: 'OPTIMAL',
    kpis: [
      { label: 'OVERALL OEE', value: '84.2%', delta: '+3.1%', deltaType: 'positive', provenance: 'SCADA_TELEMETRY' },
      { label: 'FIRST PASS YIELD (FPY)', value: '98.6%', delta: '+0.2%', deltaType: 'positive', provenance: 'QUALITY_MODULE' },
      { label: 'BOTTLENECK WORK CENTER', value: 'WC-04 (Stitching)', delta: '94% Load', deltaType: 'negative', provenance: 'CAPACITY_MODEL' },
      { label: 'UNPLANNED DOWNTIME', value: '1.2 Hrs', delta: '-45 Mins', deltaType: 'positive', provenance: 'MAINTENANCE_LOG' },
    ],
    signals: [
      { id: 'mfg-sig-1', title: 'Work Center 04 Approaching Saturation', impact: 'Queue Depth: 18 Lots', type: 'risk', severity: 'warning', actionPrompt: 'Reroute Capacity' },
    ],
    subdomains: [
      { id: 'schedule', title: 'Production Schedule', description: 'Real-time job queue dispatching, work-in-progress (WIP) tracking, and changeover matrix.', icon: Clock, metric: '14 Active', metricLabel: 'BATCH ORDERS' },
      { id: 'mrp', title: 'MRP & BOM Exploder', description: 'Multi-level Bill of Materials explosion with indented parent-child component availability.', icon: Layers, metric: '100%', metricLabel: 'MAT AVAILABILITY', badge: 'SOLVER READY' },
      { id: 'oee', title: 'OEE & Work Centers', description: 'Decomposition of machine availability, performance rate, and quality yield indices.', icon: Gauge, metric: '84.2%', metricLabel: 'COMPOSITE OEE' },
      { id: 'quality', title: 'Quality & Scrap Pareto', description: 'Defect distribution, non-conformance logging, and scrap cost root-cause analysis.', icon: ShieldAlert, metric: '1.4%', metricLabel: 'SCRAP RATE' },
    ]
  },
  'procurement': {
    domainTag: '07',
    id: 'procurement',
    title: 'Procurement Intelligence & Supply',
    description: 'Supplier OTIF evaluation, purchase price variance (PPV), vendor concentration risk, and automated purchase order generation.',
    route: '/procurement',
    icon: ShoppingCart,
    telemetryStream: 'PURCHASE ORDER ENGINE',
    status: 'OPTIMAL',
    kpis: [
      { label: 'ACTIVE SUPPLIERS', value: '48 Vendors', delta: '+2 Onboarded', deltaType: 'neutral', provenance: 'VENDOR_MASTER' },
      { label: 'PURCHASE PRICE VARIANCE', value: '-$42K (Fav)', delta: 'Under Budget', deltaType: 'positive', provenance: 'PPV_AUDIT' },
      { label: 'VENDOR OTIF AVERAGE', value: '92.4%', delta: '+1.6%', deltaType: 'positive', provenance: 'RECEIVING_DOCK' },
      { label: 'SINGLE-SOURCE EXPOSURE', value: '$840K Spend', delta: '3 Critical SKUs', deltaType: 'negative', provenance: 'RISK_ENGINE' },
    ],
    signals: [
      { id: 'proc-sig-1', title: 'Favorable Yarn Contract Window', impact: 'Est. Savings: $32K', type: 'opportunity', severity: 'info', actionPrompt: 'Review PO Recommendations' },
    ],
    subdomains: [
      { id: 'suppliers', title: 'Supplier Scorecards', description: 'Empirical supplier lead times, delivery variance percentiles, and quality scores.', icon: PieChart, metric: '92.4%', metricLabel: 'EMPIRICAL OTIF', badge: 'VERIFIED' },
      { id: 'spend', title: 'Spend Intelligence & PPV', description: 'Category spend treemaps, purchase price variance, and volume discount compliance.', icon: BarChart3, metric: '-$42K', metricLabel: 'PPV VARIANCE' },
      { id: 'orders', title: 'Purchase Orders & MOQ', description: 'Automated PO builder factoring supplier economic order quantities and container fill.', icon: PackageCheck, metric: '12 POs', metricLabel: 'AWAITING DISPATCH' },
      { id: 'risk', title: 'Supplier Risk & Assurance', description: 'Vendor financial health, ESG compliance, and dual-sourcing contingency matrices.', icon: ShieldAlert, metric: '03 SKUs', metricLabel: 'SINGLE SOURCE' },
    ]
  },
  'logistics': {
    domainTag: '08',
    id: 'logistics',
    title: 'Logistics & Freight Economics',
    description: 'Live freight shipment tracking, lane transit percentiles (P90/P95), carrier performance metrics, and dynamic demurrage prevention.',
    route: '/logistics',
    icon: Share2,
    telemetryStream: 'TMS / TELEMATICS FEED',
    status: 'OPTIMAL',
    kpis: [
      { label: 'ACTIVE SHIPMENTS', value: '64 Loads', delta: '8 In-Transit', deltaType: 'neutral', provenance: 'CARRIER_EDI' },
      { label: 'LANE ON-TIME RATE', value: '94.8%', delta: '+0.8%', deltaType: 'positive', provenance: 'GPS_TELEMETRY' },
      { label: 'AVG FREIGHT COST / KG', value: '$0.42', delta: '-4.5%', deltaType: 'positive', provenance: 'FREIGHT_AUDIT' },
      { label: 'DELAY RISK ALERTS', value: '02 Shipments', delta: 'Customs Hold', deltaType: 'negative', provenance: 'CARRIER_API' },
    ],
    signals: [
      { id: 'log-sig-1', title: 'Port Congestion Delay Alert (JNPT)', impact: '+3 Days Transit Time', type: 'risk', severity: 'warning', actionPrompt: 'Reroute Inland Carrier' },
    ],
    subdomains: [
      { id: 'shipments', title: 'Active Shipments', description: 'Real-time GPS container tracking, estimated arrival times, and milestone telemetry.', icon: Truck, metric: '64 Loads', metricLabel: 'IN-FLIGHT', badge: 'TELEMATICS' },
      { id: 'carriers', title: 'Carrier Scorecards', description: 'Carrier rate compliance, detention/demurrage incident rates, and damage claims.', icon: PieChart, metric: '94.8%', metricLabel: 'ON-TIME RATE' },
      { id: 'lanes', title: 'Lane Intelligence', description: 'Origin-destination transit duration percentiles (P50/P90/P95) and rate volatility.', icon: Network, metric: '18 Lanes', metricLabel: 'MONITORED' },
      { id: 'freight', title: 'Freight Economics', description: 'Cost per ton-mile, dynamic fuel surcharge reconciliation, and carrier invoice auditing.', icon: Landmark, metric: '$0.42/kg', metricLabel: 'WEIGHTED AVG' },
    ]
  },
  'risk-assurance': {
    domainTag: '09',
    id: 'risk-assurance',
    title: 'Enterprise Risk & Autonomous Assurance',
    description: 'Continuous financial audit, 3-way matching assurance, phantom inventory detection, duplicate invoice prevention, and disruption propagation.',
    route: '/risk-assurance',
    icon: ShieldAlert,
    telemetryStream: 'ASSURANCE AUDIT ENGINE',
    status: 'WATCH',
    kpis: [
      { label: 'DETECTED LEAKAGE EXPOSURE', value: '$48,200', delta: 'Under Remediation', deltaType: 'negative', provenance: '3WAY_MATCH' },
      { label: '3-WAY MATCHING COMPLIANCE', value: '99.4%', delta: '+0.2%', deltaType: 'positive', provenance: 'INVOICE_OCR' },
      { label: 'PHANTOM INVENTORY RISKS', value: '02 SKUs', delta: '$14K Variance', deltaType: 'negative', provenance: 'CYCLE_COUNT' },
      { label: 'COMPLIANCE AUDIT HEALTH', value: '100%', delta: 'Zero Violations', deltaType: 'positive', provenance: 'RLS_ENFORCER' },
    ],
    signals: [
      { id: 'risk-sig-1', title: 'Potential Duplicate Invoice Detected (#INV-9821)', impact: '$24,000 Payment Hold', type: 'risk', severity: 'critical', actionPrompt: 'Review Audit Finding' },
    ],
    subdomains: [
      { id: 'vulnerability', title: 'Network Vulnerability Radar', description: 'Multi-tier dependency stress tests and disruption probability modeling.', icon: ShieldAlert, metric: 'Low Risk', metricLabel: 'NETWORK STATUS' },
      { id: 'assurance', title: '3-Way Match Assurance', description: 'Autonomous PO, GRN, and Invoice three-way reconciliation with discrepancy tolerance checks.', icon: ShieldCheck, metric: '99.4%', metricLabel: 'MATCH RATE', badge: 'PHASE 20' },
      { id: 'leakage', title: 'Leakage Remediation', description: 'Unbilled shipments, duplicate payment recovery, and PPV variance clawbacks.', icon: AlertTriangle, metric: '$48.2K', metricLabel: 'PREVENTED' },
      { id: 'disruptions', title: 'Disruption Propagation', description: 'Causal impact cascade across downstream customers and financial margin commitments.', icon: Network, metric: '02 Active', metricLabel: 'SIMULATED CASCADES' },
    ]
  },
  'processes': {
    domainTag: '10',
    id: 'processes',
    title: 'Process Mining & Workflow Intelligence',
    description: 'Object-Centric Process Mining (OCPM), path variant discovery, rework loop detection, and process SLA conformance auditing.',
    route: '/processes',
    icon: GitFork,
    telemetryStream: 'EVENT LOG COLLECTOR',
    status: 'OPTIMAL',
    kpis: [
      { label: 'AVERAGE CYCLE TIME', value: '4.2 Days', delta: '-0.8 Days', deltaType: 'positive', provenance: 'OCPM_ENGINE' },
      { label: 'HAPPY PATH CONFORMANCE', value: '88.4%', delta: '+4.2%', deltaType: 'positive', provenance: 'PROCESS_GRAPH' },
      { label: 'REWORK LOOP RATE', value: '3.1%', delta: '-1.2%', deltaType: 'positive', provenance: 'EVENT_STREAM' },
      { label: 'SLA BOTTLENECK VIOLATIONS', value: '04 Events', delta: 'Within Threshold', deltaType: 'neutral', provenance: 'SLA_MONITOR' },
    ],
    signals: [
      { id: 'prc-sig-1', title: 'Approval Stage Rework Loop', impact: 'Adds 1.4 days to PO cycle', type: 'risk', severity: 'warning', actionPrompt: 'Inspect Process Graph' },
    ],
    subdomains: [
      { id: 'mining', title: 'Process Mining & Flow', description: 'Directed acyclic graph visualization of end-to-end operational execution paths.', icon: GitFork, metric: '88.4%', metricLabel: 'CONFORMANCE', badge: 'OCPM' },
      { id: 'variants', title: 'Variant Discovery', description: 'Execution variant frequency distribution, deviant pathways, and root-cause drivers.', icon: Workflow, metric: '14 Paths', metricLabel: 'DISCOVERED' },
      { id: 'bottlenecks', title: 'Bottleneck SLAs', description: 'Queue duration percentiles by station with SLA threshold violation telemetry.', icon: Clock, metric: 'WC-04', metricLabel: 'PRIMARY BOTTLENECK' },
      { id: 'cycle-time', title: 'Cycle-Time Distribution', description: 'Order-to-cash and procure-to-pay duration histograms and variance drivers.', icon: BarChart3, metric: '4.2 Days', metricLabel: 'MEDIAN TIME' },
    ]
  },
  'decisions': {
    domainTag: '11',
    id: 'decisions',
    title: 'Autonomous Decisions & Prescriptions',
    description: 'Prescriptive decision engine generating ranked trade-off candidates with Expected Value (EV), confidence intervals, and preflight governance.',
    route: '/decisions',
    icon: Target,
    telemetryStream: 'PRESCRIPTIVE SOLVER',
    status: 'OPTIMAL',
    kpis: [
      { label: 'PENDING PRESCRIPTIONS', value: '06 Actions', delta: 'High Confidence', deltaType: 'positive', provenance: 'DECISION_ENGINE' },
      { label: 'PROJECTED VALUE GAIN', value: '+$142K', delta: 'Annualized', deltaType: 'positive', provenance: 'EV_OPTIMIZER' },
      { label: 'EXECUTION SUCCESS RATE', value: '99.8%', delta: 'Zero Rollbacks', deltaType: 'positive', provenance: 'ACTION_CENTER' },
      { label: 'PREFLIGHT CLEARANCE', value: '100% Passed', delta: 'Policy Governed', deltaType: 'positive', provenance: 'GOVERNANCE_GATE' },
    ],
    signals: [
      { id: 'dec-sig-1', title: 'Multi-Echelon Buffer Rebalance Available', impact: 'EV: +$38,400 | Conf: 94%', type: 'opportunity', severity: 'info', actionPrompt: 'Execute Preflight Clearance' },
    ],
    subdomains: [
      { id: 'feed', title: 'Prescriptive Decision Feed', description: 'Ranked candidate actions with Expected Value, trade-off analysis, and risk scoring.', icon: Target, metric: '06 Ready', metricLabel: 'CANDIDATES', badge: 'PHASE 27' },
      { id: 'tradeoffs', title: 'Trade-off & Frontier Analysis', description: 'Pareto frontier of service level vs. working capital cost tradeoff curves.', icon: Scale, metric: '+$142K', metricLabel: 'EXPECTED VALUE' },
      { id: 'preflight', title: 'Preflight Gate & Clearances', description: 'Automated cryptographic security, policy conformance, and RLS constraint verification.', icon: ShieldCheck, metric: 'PASSED', metricLabel: 'GATE STATUS' },
      { id: 'history', title: 'Action Execution History', description: 'Audit log of executed prescriptions, measured value realization, and outcome learning.', icon: FileText, metric: '100%', metricLabel: 'VERIFIED' },
    ]
  },
  'scenarios': {
    domainTag: '12',
    id: 'scenarios',
    title: 'What-If Simulation Twin & Scenarios',
    description: 'Deterministic supply chain shocks, Monte Carlo stochastic simulations, P50/P90 financial distribution curves, and counterfactual analysis.',
    route: '/scenarios',
    icon: TestTube,
    telemetryStream: 'DIGITAL TWIN SIMULATOR',
    status: 'OPTIMAL',
    kpis: [
      { label: 'SIMULATION FIDELITY', value: '99.2%', delta: 'Calibrated to Live', deltaType: 'positive', provenance: 'TWIN_STATE' },
      { label: 'MONTE CARLO ITERATIONS', value: '10,000 Runs', delta: 'Convergence Reached', deltaType: 'neutral', provenance: 'SIMULATION_WORKER' },
      { label: 'P90 MAXIMUM EXPOSURE', value: '$240K', delta: 'Shock: +20% Demand', deltaType: 'neutral', provenance: 'P90_SOLVER' },
      { label: 'COUNTERFACTUAL MODELS', value: '08 Active', delta: 'Trained', deltaType: 'positive', provenance: 'CAUSAL_AI' },
    ],
    signals: [
      { id: 'scn-sig-1', title: 'Port Disruption Shock Simulation Ready', impact: 'P50 Margin Impact: -$18K', type: 'alert', severity: 'info', actionPrompt: 'Run Monte Carlo Analysis' },
    ],
    subdomains: [
      { id: 'simulator', title: 'What-If Twin Simulator', description: 'Interactive shock override parameters for lead time, demand spikes, and cost inflation.', icon: TestTube, metric: '99.2%', metricLabel: 'FIDELITY', badge: 'DIGITAL TWIN' },
      { id: 'monte-carlo', title: 'Monte Carlo & Distributions', description: 'P50, P75, and P90 probability distribution curves across financial and service KPIs.', icon: LineChart, metric: '10k Runs', metricLabel: 'ITERATIONS', badge: 'STOCHASTIC' },
      { id: 'counterfactuals', title: 'Counterfactual Analysis', description: 'Root-cause causal attribution isolating past policy decisions from macro market shifts.', icon: Network, metric: '08 Active', metricLabel: 'MODELS' },
      { id: 'comparison', title: 'Scenario Comparison Bridge', description: 'Side-by-side delta waterfalls comparing candidate future policies against baseline.', icon: BarChart3, metric: '+$84K', metricLabel: 'DELTA VARIANCE' },
    ]
  },
  'agents': {
    domainTag: '13',
    id: 'agents',
    title: 'Autonomous AI Agents & Studio',
    description: 'Autonomous agent runtime fleet, execution journals, tool-calling telemetry, safety guardrails, and visual Multi-Agent DAG Studio.',
    route: '/agent-studio',
    icon: Bot,
    telemetryStream: 'AGENT RUNTIME ORCHESTRATOR',
    status: 'OPTIMAL',
    kpis: [
      { label: 'ACTIVE AGENT FLEET', value: '08 Agents', delta: '100% Operational', deltaType: 'positive', provenance: 'AGENT_RUNTIME' },
      { label: 'AUTONOMOUS ACTIONS (24H)', value: '142 Executed', delta: '+22.4%', deltaType: 'positive', provenance: 'ACTION_LEDGER' },
      { label: 'GUARDRAIL VERIFICATION', value: '100%', delta: 'Zero Violations', deltaType: 'positive', provenance: 'CIRCUIT_BREAKER' },
      { label: 'AI TOKEN BUDGET USAGE', value: '42.8%', delta: 'Under Quota', deltaType: 'positive', provenance: 'QUOTA_RESERVATION' },
    ],
    signals: [
      { id: 'agt-sig-1', title: 'Inventory Rebalancing Agent Triggered', impact: 'Executed 12 Stock Transits', type: 'opportunity', severity: 'info', actionPrompt: 'Inspect Execution Journal' },
    ],
    subdomains: [
      { id: 'fleet', title: 'Agent Fleet Runtime', description: 'Live status, heartbeat, memory buffers, and active tool attachments for all autonomous workers.', icon: Bot, metric: '08 Active', metricLabel: 'FLEET SIZE', badge: 'AUTONOMOUS' },
      { id: 'execution', title: 'Execution Journal & Stream', description: 'Step-by-step reasoning traces, function call arguments, and verified response payloads.', icon: Terminal, metric: '142 Tasks', metricLabel: 'COMPLETED 24H' },
      { id: 'governance', title: 'Guardrails & AI Quotas', description: 'Token budget limits, circuit breaker trips, idempotency keys, and human-in-the-loop approvals.', icon: ShieldCheck, metric: '42.8%', metricLabel: 'QUOTA USED' },
      { id: 'studio', title: 'Agent Studio & DAG Builder', description: 'Visual multi-agent workflow designer, prompt linting, and declarative DAG deployment.', icon: Workflow, metric: '04 DAGs', metricLabel: 'DEPLOYED', badge: 'STUDIO' },
    ]
  },
  'data-integrations': {
    domainTag: '14',
    id: 'data-integrations',
    title: 'Data Fabric, Ingestion & Lineage',
    description: 'Enterprise connector hub (SAP, Odoo, Tally), canonical entity intake, source-to-target data lineage, and multi-source reconciliation.',
    route: '/data-integrations',
    icon: Database,
    telemetryStream: 'DATA PIPELINE FABRIC',
    status: 'OPTIMAL',
    kpis: [
      { label: 'INTEGRATION CONNECTORS', value: '04 Active', delta: 'SAP/Odoo/Tally/TMS', deltaType: 'positive', provenance: 'CONNECTOR_HUB' },
      { label: 'DATA RECONCILIATION RATE', value: '99.92%', delta: '+0.04%', deltaType: 'positive', provenance: 'RECONCILIATION_ENGINE' },
      { label: 'INGESTION RUN HEALTH', value: '100% Passed', delta: 'Zero Quarantine', deltaType: 'positive', provenance: 'INTAKE_PIPELINE' },
      { label: 'FRESHNESS LATENCY', value: '< 2 Mins', delta: 'Streaming Sync', deltaType: 'positive', provenance: 'TELEMETRY_TRACKER' },
    ],
    signals: [
      { id: 'dat-sig-1', title: 'SAP S/4HANA Sync Nominal', impact: '24,000 Records Ingested', type: 'opportunity', severity: 'info', actionPrompt: 'View Lineage Graph' },
    ],
    subdomains: [
      { id: 'connectors', title: 'Connector Hub', description: 'Live status, credentials, and polling schedules for ERP, TMS, and CRM integrations.', icon: Database, metric: '04 Active', metricLabel: 'CONNECTORS', badge: 'ENTERPRISE' },
      { id: 'ingestion', title: 'Ingestion Pipeline & Intake', description: 'Batch file intake, schema validation, quarantine management, and canonical mapping.', icon: PackageCheck, metric: '100%', metricLabel: 'INTAKE HEALTH', route: '/data/intake' },
      { id: 'quality', title: 'Data Quality & Validation', description: 'Field-level completeness, validity, and consistency scoring across canonical entities.', icon: Scale, metric: 'Monitored', metricLabel: 'QUALITY SCORE', route: '/data/quality' },
      { id: 'lineage', title: 'Lineage & Provenance Graph', description: 'Field-level source authority, transform provenance, and cryptographic verification stamps.', icon: GitFork, metric: 'Verified', metricLabel: 'PROVENANCE', badge: 'TRACEABILITY' },
      { id: 'reconciliation', title: 'Multi-Source Reconciliation', description: 'Automated entity resolution and discrepancy adjudication across disparate ERP systems.', icon: Scale, metric: '99.92%', metricLabel: 'MATCH RATE' },
    ]
  },
  'admin': {
    domainTag: '15',
    id: 'admin',
    title: 'Governance, Security & System Control',
    description: 'Row-Level Security (RLS) enforcement, user RBAC permissions, audit ledgers, tenant configuration, and platform health telemetry.',
    route: '/admin',
    icon: Sliders,
    telemetryStream: 'SECURITY & GOVERNANCE GATE',
    status: 'OPTIMAL',
    kpis: [
      { label: 'SECURITY ENFORCEMENT', value: 'RLS ACTIVE', delta: 'Tenant Isolated', deltaType: 'positive', provenance: 'POSTGRES_RLS' },
      { label: 'AUTHENTICATED USERS', value: '18 Operators', delta: 'RBAC Enforced', deltaType: 'neutral', provenance: 'AUTH_SERVICE' },
      { label: 'IMMUTABLE AUDIT LOGS', value: '14,280 Events', delta: 'Cryptographically Sealed', deltaType: 'positive', provenance: 'AUDIT_LEDGER' },
      { label: 'SYSTEM CPU / MEMORY', value: '14% / 28%', delta: 'Optimal', deltaType: 'positive', provenance: 'INFRA_MONITOR' },
    ],
    signals: [
      { id: 'adm-sig-1', title: 'Tenant Boundary Verification', impact: 'Zero Cross-Tenant Leaks', type: 'opportunity', severity: 'info', actionPrompt: 'Inspect Security Ledger' },
    ],
    subdomains: [
      { id: 'governance', title: 'Governance & RBAC', description: 'User roles, approver hierarchies, permission matrix administration, and the immutable audit ledger.', icon: ShieldCheck, metric: '18 Users', metricLabel: 'CONFIGURED', badge: 'SECURITY', route: '/admin/users' },
      { id: 'models', title: 'MLOps Model Registry', description: 'Champion/challenger model tracking, drift status, and retraining triggers.', icon: Gauge, metric: '5 Models', metricLabel: 'REGISTERED', route: '/admin/models' },
      { id: 'integrations', title: 'Integration Center', description: 'ERP, WMS, TMS and commerce connector health, sync frequency, and error rates.', icon: Shield, metric: '4 Connectors', metricLabel: 'ACTIVE', route: '/admin/integrations' },
      { id: 'system-health', title: 'System Health', description: 'Infrastructure telemetry, service uptime, and platform-wide operational status.', icon: FileText, metric: 'OPERATIONAL', metricLabel: 'STATUS', route: '/admin/system-health' },
    ]
  },
};
