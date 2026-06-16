import { getDashboardData } from "@/lib/data";
import Dashboard from "@/components/Dashboard";

export default function Page() {
  const data = getDashboardData();
  return <Dashboard data={data} />;
}
