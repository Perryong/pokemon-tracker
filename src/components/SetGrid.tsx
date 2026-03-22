import React, { useMemo, useState } from 'react';
import { format } from 'date-fns';
import { PokemonSet, useSets, useSeries } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { CalendarIcon, Search } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface SetGridProps {
  onSetSelect: (set: PokemonSet) => void;
}

const FALLBACK_SET_IMAGE =
  'data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"180\" viewBox=\"0 0 320 180\"><rect width=\"320\" height=\"180\" rx=\"12\" fill=\"%23f4f4f5\"/><text x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" fill=\"%23a1a1aa\" font-family=\"Inter,Arial\" font-size=\"16\">No Set Logo</text></svg>';

const SetGrid: React.FC<SetGridProps> = ({ onSetSelect }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [legalityFilter, setLegalityFilter] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date | undefined>(undefined);
  const [endDate, setEndDate] = useState<Date | undefined>(undefined);
  const [seriesFilter, setSeriesFilter] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const pageSize = 20;

  // Build filters object based on selected filters
  const filters: Record<string, string> = {};
  
  if (legalityFilter) {
    if (legalityFilter === 'standard') {
      filters['legalities.standard'] = 'legal';
    } else if (legalityFilter === 'expanded') {
      filters['legalities.expanded'] = 'legal';
    }
  }
  
  if (startDate && endDate) {
    filters['releaseDate'] = `gte${format(startDate, 'yyyy/MM/dd')} lte${format(endDate, 'yyyy/MM/dd')}`;
  } else if (startDate) {
    filters['releaseDate'] = `gte${format(startDate, 'yyyy/MM/dd')}`;
  } else if (endDate) {
    filters['releaseDate'] = `lte${format(endDate, 'yyyy/MM/dd')}`;
  }

  const { sets, totalSets, loading, error } = useSets(currentPage, pageSize, filters);
  const { ownedCards, cardQuantities } = useCollection();
  const { series } = useSeries();
  const totalPages = Math.ceil(totalSets / pageSize);

  const completionBySet = useMemo(() => {
    const completionMap: Record<
      string,
      { owned: number; percentage: number; total: number; totalQuantity: number }
    > = {};

    const ownedCountBySet: Record<string, number> = {};
    const quantityBySet: Record<string, number> = {};
    
    // Count unique owned and sum quantities per set
    Object.entries(cardQuantities).forEach(([cardId, qty]) => {
      if (qty <= 0) return;
      const [setId] = cardId.split('-');
      if (!setId) return;
      ownedCountBySet[setId] = (ownedCountBySet[setId] ?? 0) + 1;
      quantityBySet[setId] = (quantityBySet[setId] ?? 0) + qty;
    });

    sets.forEach((set) => {
      const total = typeof set.total === 'number' ? set.total : 0;
      const owned = ownedCountBySet[set.id] ?? 0;
      const rawPercentage = total > 0 ? (owned / total) * 100 : 0;
      const percentage = Math.min(Math.max(rawPercentage, 0), 100);
      const totalQuantity = quantityBySet[set.id] ?? 0;
      completionMap[set.id] = { owned, percentage, total, totalQuantity };
    });

    return completionMap;
  }, [sets, cardQuantities]);

  // Filter by series (most restrictive first)
  const filteredBySeries = useMemo(() => {
    if (!seriesFilter) return sets;
    return sets.filter(set => set.series === seriesFilter);
  }, [sets, seriesFilter]);

  // Filter by search query
  const filteredBySearch = useMemo(() => {
    if (!searchQuery.trim()) return filteredBySeries;
    const query = searchQuery.toLowerCase().trim();
    return filteredBySeries.filter(set => 
      set.name.toLowerCase().includes(query)
    );
  }, [filteredBySeries, searchQuery]);

  const getCompletion = (setId: string, total: number | undefined) => {
    return (
      completionBySet[setId] ?? {
        owned: 0,
        percentage: 0,
        total: typeof total === 'number' ? total : 0,
        totalQuantity: 0,
      }
    );
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo(0, 0);
  };

  const clearFilters = () => {
    setLegalityFilter(null);
    setStartDate(undefined);
    setEndDate(undefined);
    setSeriesFilter(null);
    setSearchQuery('');
  };

  if (error) {
    return (
      <div className="flex flex-col items-center p-8 bg-red-50 rounded-lg text-red-800">
        <h2 className="text-2xl font-bold mb-2">Error Loading Sets</h2>
        <p>{error.message}</p>
        <Button onClick={() => window.location.reload()} className="mt-4 bg-red-600 hover:bg-red-700">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">Pokémon TCG Sets</h1>
        
        <div className="flex flex-wrap gap-2">
          <Select 
            value={seriesFilter || "all"} 
            onValueChange={(value) => setSeriesFilter(value === "all" ? null : value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Series" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Series</SelectItem>
              {series.map(s => (
                <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search sets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 w-[200px]"
            />
          </div>
          
          <Select value={legalityFilter || "none"} onValueChange={(value) => setLegalityFilter(value === "none" ? null : value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Format Legality" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">All Sets</SelectItem>
              <SelectItem value="standard">Standard Legal</SelectItem>
              <SelectItem value="expanded">Expanded Legal</SelectItem>
            </SelectContent>
          </Select>
          
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-[240px] justify-start text-left font-normal",
                  (startDate || endDate) && "text-primary"
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {startDate && endDate ? (
                  <>
                    {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
                  </>
                ) : startDate ? (
                  <>From {format(startDate, 'MMM d, yyyy')}</>
                ) : endDate ? (
                  <>Until {format(endDate, 'MMM d, yyyy')}</>
                ) : (
                  <>Release Date Range</>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="range"
                selected={{
                  from: startDate,
                  to: endDate,
                }}
                onSelect={(range) => {
                  setStartDate(range?.from);
                  setEndDate(range?.to);
                }}
                initialFocus
              />
            </PopoverContent>
          </Popover>
          
          {(legalityFilter || startDate || endDate || seriesFilter || searchQuery) && (
            <Button variant="ghost" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </div>
      </div>

      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, index) => (
            <Card key={index} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="p-4">
                  <Skeleton className="h-40 w-full mb-4" />
                  <Skeleton className="h-6 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-1/2 mb-2" />
                  <Skeleton className="h-4 w-1/3" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!loading && filteredBySearch.length === 0 && (
        <div className="text-center p-8 bg-muted rounded-lg">
          <h2 className="text-2xl font-semibold mb-2">No Sets Found</h2>
          <p className="mb-4 text-muted-foreground">
            No Pokémon card sets match your current filters.
          </p>
          <Button onClick={clearFilters}>Clear Filters</Button>
        </div>
      )}

      {!loading && filteredBySearch.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {filteredBySearch.map((set) => {
              const completion = getCompletion(set.id, set.total);

              return (
                <Card
                  key={set.id}
                  className="overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
                  onClick={() => onSetSelect(set)}
                >
                  <div className="h-52 bg-muted flex items-center justify-center p-4">
                    <img
                      src={set.images.logo || FALLBACK_SET_IMAGE}
                      alt={`${set.name} logo`}
                      className="max-h-full max-w-full object-contain"
                      loading="lazy"
                      onError={(e) => {
                        if (e.currentTarget.src !== FALLBACK_SET_IMAGE) {
                          e.currentTarget.src = FALLBACK_SET_IMAGE;
                        } else {
                          e.currentTarget.style.display = 'none';
                        }
                      }}
                    />
                  </div>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-bold line-clamp-1">{set.name}</h3>
                      {set.images.symbol && (
                        <img
                          src={set.images.symbol}
                          alt={`${set.name} symbol`}
                          className="h-6 w-6"
                          loading="lazy"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      Released: {set.releaseDate ? format(new Date(set.releaseDate), 'MMM d, yyyy') : 'Unknown'}
                    </p>
                    <div className="space-y-2 mb-4">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-sm">
                        <span className="font-medium">
                          Owned {completion.owned} / {completion.total}
                        </span>
                        <span className="text-xs uppercase tracking-wide text-muted-foreground">
                          {completion.percentage.toFixed(0)}%
                        </span>
                      </div>
                      {/* Total quantity supplement - only show if there are duplicates */}
                      {completion.totalQuantity > completion.owned && (
                        <div className="text-xs text-muted-foreground">
                          Total Qty: {completion.totalQuantity}
                        </div>
                      )}
                      <Progress
                        value={completion.percentage}
                        aria-label={`Owned ${completion.owned} of ${completion.total} cards in ${set.name}`}
                      />
                    </div>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap gap-1">
                        {set.legalities?.standard === 'legal' && (
                          <Badge variant="default" className="bg-green-600">
                            Standard
                          </Badge>
                        )}
                        {set.legalities?.expanded === 'legal' && (
                          <Badge variant="secondary">Expanded</Badge>
                        )}
                      </div>
                      {completion.percentage === 100 && (
                        <Badge 
                          className="border-emerald-500 bg-emerald-100 text-emerald-700 font-semibold" 
                          variant="outline"
                        >
                          ✓ Complete
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {totalPages > 1 && !seriesFilter && !searchQuery && (
            <Pagination className="my-8">
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious 
                    onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
                
                {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                  let pageNumber;
                  
                  // Show first page, last page, current page, and pages around current
                  if (totalPages <= 5) {
                    pageNumber = i + 1;
                  } else if (currentPage <= 3) {
                    pageNumber = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNumber = totalPages - 4 + i;
                  } else {
                    pageNumber = currentPage - 2 + i;
                  }
                  
                  if (pageNumber === 1 || pageNumber === totalPages || 
                      (pageNumber >= currentPage - 1 && pageNumber <= currentPage + 1)) {
                    return (
                      <PaginationItem key={i}>
                        <PaginationLink
                          isActive={pageNumber === currentPage}
                          onClick={() => handlePageChange(pageNumber)}
                        >
                          {pageNumber}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  }
                  
                  if (pageNumber === 2 || pageNumber === totalPages - 1) {
                    return (
                      <PaginationItem key={i}>
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                  }
                  
                  return null;
                })}
                
                <PaginationItem>
                  <PaginationNext 
                    onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}
    </div>
  );
};

export default SetGrid;
