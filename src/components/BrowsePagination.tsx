import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
export default function BrowsePagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) {
  if (pages <= 1) return null;
  return <nav className="page-pagination" aria-label="pagination"><span>Page <strong>{page}</strong> of {pages}</span><div className="page-buttons"><Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}><ArrowLeft size={14} className="mr-2" />Previous</Button><Button variant="outline" size="sm" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next<ArrowRight size={14} className="ml-2" /></Button></div></nav>;
}
