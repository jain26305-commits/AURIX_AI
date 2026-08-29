import { ApiClient } from "@/services/api/apiClient";

export interface SearchResultItem {
  id: string;
  title: string;
  subtitle: string;
  category: "CUSTOMERS" | "SUPPLIERS" | "SKUS" | "DECISIONS" | "AGENTS" | "WORKFLOWS" | "DOMAINS";
  route: string;
  riskTier?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface SearchResponseDTO {
  query: string;
  totalResults: number;
  results: SearchResultItem[];
}

export class SearchService {
  public static async queryEntities(searchTerm: string): Promise<SearchResultItem[]> {
    if (!searchTerm || searchTerm.trim().length === 0) {
      return [];
    }

    return ApiClient.get<SearchResultItem[]>(
      `/search?q=${encodeURIComponent(searchTerm)}`,
      () => {
        // Fallback in-memory search resolver matching query across registered entities
        const q = searchTerm.toLowerCase();
        const catalog: SearchResultItem[] = [
          { id: "CUST-APEX", title: "Apex Global Corp", subtitle: "Customer Account • $4.2M YTD • Tier A", category: "CUSTOMERS", route: "/sales" },
          { id: "CUST-DELTA", title: "Delta Logistics", subtitle: "Customer Account • $1.85M YTD • Tier A", category: "CUSTOMERS", route: "/sales" },
          { id: "SUPP-PREC", title: "Precision Parts Ltd", subtitle: "Certified Vendor • 12d Lead Time • High PPV", category: "SUPPLIERS", route: "/procurement" },
          { id: "SUPP-STEEL", title: "Global Steel Works", subtitle: "Primary Vendor • 24d Lead Time", category: "SUPPLIERS", route: "/procurement" },
          { id: "SKU-PUMP-01", title: "SKU-PUMP-01 (Hydraulic Pump V2)", subtitle: "Inventory SKU • Plant Antwerp • Shortage Risk", category: "SKUS", route: "/inventory", riskTier: "HIGH" },
          { id: "SKU-VALVE-04", title: "SKU-VALVE-04 (Control Valve)", subtitle: "Inventory SKU • Plant Munich • Healthy Stock", category: "SKUS", route: "/inventory" },
          { id: "DEC-PO-SPLIT-101", title: "DEC-PO-SPLIT-101", subtitle: "Reallocate PO-4001 Volume • +$42,000 EV", category: "DECISIONS", route: "/decisions", riskTier: "LOW" },
          { id: "DEC-INV-HOLD-102", title: "DEC-INV-HOLD-102", subtitle: "Credit Hold on Apex Global • +$85,000 EV", category: "DECISIONS", route: "/decisions", riskTier: "MEDIUM" },
          { id: "AGT-FIN-01", title: "Working Capital & Finance Agent", subtitle: "Autonomous Agent • 97.6% Success Rate", category: "AGENTS", route: "/agents" },
          { id: "AGT-PROC-01", title: "Procurement & Supplier Agent", subtitle: "Autonomous Agent • High Autonomy", category: "AGENTS", route: "/agents", riskTier: "HIGH" },
        ];

        return catalog.filter(
          (c) =>
            c.title.toLowerCase().includes(q) ||
            c.subtitle.toLowerCase().includes(q) ||
            c.category.toLowerCase().includes(q)
        );
      }
    );
  }
}
