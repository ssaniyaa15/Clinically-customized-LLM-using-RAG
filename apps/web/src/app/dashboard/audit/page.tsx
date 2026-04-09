import { ActionPanel } from "@/components/dashboard/action-panel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getAuditTrail, getLatestRecommendation } from "@/lib/api/client";

export default async function DashboardAuditPage({
  searchParams,
}: {
  searchParams: { page?: string; patient_id?: string };
}): Promise<JSX.Element> {
  const patientId = searchParams.patient_id ?? "patient-001";
  const page = Number(searchParams.page ?? "1");
  const limit = 10;
  const offset = (page - 1) * limit;
  const [rows, gated] = await Promise.all([getAuditTrail(offset, limit), getLatestRecommendation(patientId)]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Audit Trail</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Clinician</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead>Signature</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, idx) => (
                <TableRow key={`${row.patient_id}-${idx}`}>
                  <TableCell>{row.patient_id}</TableCell>
                  <TableCell>{row.clinician_id}</TableCell>
                  <TableCell>{row.action_taken}</TableCell>
                  <TableCell>{new Date(row.timestamp).toLocaleString()}</TableCell>
                  <TableCell className="font-mono text-xs">{row.electronic_signature_hash.slice(0, 12)}...</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>Page {page}</span>
            <div className="flex gap-2">
              <a className="rounded border px-3 py-1" href={`/dashboard/audit?page=${Math.max(1, page - 1)}`}>
                Prev
              </a>
              <a className="rounded border px-3 py-1" href={`/dashboard/audit?page=${page + 1}`}>
                Next
              </a>
            </div>
          </div>
          <ActionPanel recommendation={gated} patientId={patientId} />
        </CardContent>
      </Card>
    </div>
  );
}

