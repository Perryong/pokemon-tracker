import React, { useState, useMemo } from 'react';
import { PokemonCard, PokemonSet, useCards } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ArrowLeft, ChevronDown, Filter, Plus, Check, Loader2, Search } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from '@/components/ui/pagination';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { cn } from '@/lib/utils';

interface CardGridProps {
  selectedSet: PokemonSet;
  onBackClick: () => void;
  onCardSelect: (card: PokemonCard) => void;
}

const CardGrid: React.FC<CardGridProps> = ({ selectedSet, onBackClick, onCardSelect }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [subtypeFilter, setSubtypeFilter] = useState<string | null>(null);
  const [rarityFilter, setRarityFilter] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [processingCards, setProcessingCards] = useState<Set<string>>(new Set());
  const [sizeMode, setSizeMode] = useState<'small' | 'medium'>('medium');
  const [ownershipFilter, setOwnershipFilter] = useState<'all' | 'owned' | 'missing'>('all');
  const [nameSearch, setNameSearch] = useState('');
  const pageSize = 20;

  const { toast } = useToast();
  const { 
    isInCollection, 
    addToCollection, 
    removeFromCollection 
  } = useCollection();

  // Build filters for the API request
  const filters: Record<string, string> = {};
  if (typeFilter) filters['types'] = typeFilter;
  if (subtypeFilter) filters['subtypes'] = subtypeFilter;
  if (rarityFilter) filters['rarity'] = rarityFilter;

  const { cards, totalCards, loading, error } = useCards(selectedSet.id, currentPage, pageSize, filters);

  const totalPages = Math.ceil(totalCards / pageSize);

  // Client-side filtering for ownership and name search
  const filteredCards = useMemo(() => {
    let filtered = cards;
    
    // Ownership filter
    if (ownershipFilter === 'owned') {
      filtered = filtered.filter(card => isInCollection(card.id));
    } else if (ownershipFilter === 'missing') {
      filtered = filtered.filter(card => !isInCollection(card.id));
    }
    
    // Name search (case-insensitive)
    if (nameSearch.trim()) {
      const searchLower = nameSearch.toLowerCase();
      filtered = filtered.filter(card => 
        card.name.toLowerCase().includes(searchLower)
      );
    }
    
    return filtered;
  }, [cards, ownershipFilter, nameSearch, isInCollection]);

  // Compute stats from FILTERED dataset for consistency with visible cards
  const stats = useMemo(() => {
    const total = filteredCards.length;
    const owned = filteredCards.filter(card => isInCollection(card.id)).length;
    const missing = total - owned;
    const percentage = total > 0 ? (owned / total) * 100 : 0;
    return { owned, missing, total, percentage };
  }, [filteredCards, isInCollection]);

  // Track if any client-side filters are active (for hiding pagination)
  const hasClientFilters = ownershipFilter !== 'all' || nameSearch.trim() !== '';

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo(0, 0);
  };

  const clearFilters = () => {
    setTypeFilter(null);
    setSubtypeFilter(null);
    setRarityFilter(null);
    setOwnershipFilter('all');
    setNameSearch('');
  };

  const handleAddToCollection = async (card: PokemonCard, e: React.MouseEvent) => {
    e.stopPropagation();
    setProcessingCards(prev => new Set(prev).add(card.id));
    
    try {
      await addToCollection(card.id);
      toast({
        title: "Card Added",
        description: `${card.name} has been added to your collection.`,
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add card to collection.",
        variant: "destructive",
      });
    } finally {
      setProcessingCards(prev => {
        const next = new Set(prev);
        next.delete(card.id);
        return next;
      });
    }
  };

  const handleRemoveFromCollection = async (card: PokemonCard, e: React.MouseEvent) => {
    e.stopPropagation();
    setProcessingCards(prev => new Set(prev).add(card.id));
    
    try {
      await removeFromCollection(card.id);
      toast({
        title: "Card Removed",
        description: `${card.name} has been removed from your collection.`,
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove card from collection.",
        variant: "destructive",
      });
    } finally {
      setProcessingCards(prev => {
        const next = new Set(prev);
        next.delete(card.id);
        return next;
      });
    }
  };

  // Get unique card types, subtypes, and rarities from current cards
  const uniqueTypes = Array.from(new Set(cards.flatMap(card => card.types || [])));
  const uniqueSubtypes = Array.from(new Set(cards.flatMap(card => card.subtypes || [])));
  const uniqueRarities = Array.from(new Set(cards.map(card => card.rarity).filter(Boolean) as string[]));

  const fallbackCardImage =
    'data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"260\" height=\"360\" viewBox=\"0 0 260 360\"><rect width=\"260\" height=\"360\" rx=\"16\" fill=\"%23f4f4f5\"/><text x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" fill=\"%23a1a1aa\" font-family=\"Inter,Arial\" font-size=\"16\">Image Unavailable</text></svg>';

  const gridClasses = {
    small: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2',
    medium: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4'
  };

  if (error) {
    return (
      <div className="flex flex-col items-center p-8 bg-red-50 rounded-lg text-red-800">
        <h2 className="text-2xl font-bold mb-2">Error Loading Cards</h2>
        <p>{error.message}</p>
        <div className="flex gap-4 mt-4">
          <Button onClick={() => window.location.reload()} className="bg-red-600 hover:bg-red-700">
            Retry
          </Button>
          <Button variant="outline" onClick={onBackClick}>
            Back to Sets
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl pb-24">
      <div className="sticky top-14 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 pb-6">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="outline" size="icon" onClick={onBackClick}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              {selectedSet.name}
              {selectedSet.images.symbol ? (
                <img 
                  src={selectedSet.images.symbol} 
                  alt={`${selectedSet.name} symbol`} 
                  className="h-6 w-6"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              ) : null}
            </h1>
            <p className="text-sm text-muted-foreground">
              {selectedSet.total} cards in this set
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 mb-4">
          {/* Size Toggle */}
          <Select value={sizeMode} onValueChange={(v) => setSizeMode(v as 'small' | 'medium')}>
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="small">Small</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
            </SelectContent>
          </Select>

          {/* Ownership Filter */}
          <Select value={ownershipFilter} onValueChange={(v) => setOwnershipFilter(v as 'all' | 'owned' | 'missing')}>
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="owned">Owned</SelectItem>
              <SelectItem value="missing">Missing</SelectItem>
            </SelectContent>
          </Select>

          {/* Name Search */}
          <div className="relative flex-1 min-w-[200px] max-w-[300px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={nameSearch}
              onChange={(e) => setNameSearch(e.target.value)}
              placeholder="Search cards..."
              className="pl-9"
            />
          </div>
        </div>

        <div className="mb-6">
          <Button 
            variant="outline" 
            onClick={() => setShowFilters(!showFilters)}
            className="w-full sm:w-auto flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
            <ChevronDown className={cn(
              "h-4 w-4 transition-transform",
              showFilters && "transform rotate-180"
            )} />
          </Button>
          
          {showFilters && (
            <div className="bg-card border rounded-lg mt-2 p-4">
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="card-type">
                  <AccordionTrigger>Card Type</AccordionTrigger>
                  <AccordionContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <Select value={typeFilter || "none"} onValueChange={(value) => setTypeFilter(value === "none" ? null : value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select Type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">All Types</SelectItem>
                          {uniqueTypes.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      <Select value={subtypeFilter || "none"} onValueChange={(value) => setSubtypeFilter(value === "none" ? null : value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select Subtype" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">All Subtypes</SelectItem>
                          {uniqueSubtypes.map(subtype => (
                            <SelectItem key={subtype} value={subtype}>{subtype}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      <Select value={rarityFilter || "none"} onValueChange={(value) => setRarityFilter(value === "none" ? null : value)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select Rarity" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">All Rarities</SelectItem>
                          {uniqueRarities.map(rarity => (
                            <SelectItem key={rarity} value={rarity}>{rarity}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                </Accordion>
              
              <div className="flex justify-end mt-4">
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  Clear Filters
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className={cn("grid", gridClasses[sizeMode])}>
          {Array.from({ length: 20 }).map((_, index) => (
            <Card key={index}>
              <CardContent className={cn("p-3", sizeMode === 'small' && "p-2")}>
                <Skeleton className="h-64 w-full mb-4" />
                <Skeleton className="h-5 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2 mb-2" />
                <Skeleton className="h-4 w-1/4" />
              </CardContent>
            </Card>
          ))}
        </div>
       ) : filteredCards.length === 0 ? (
        <div className="text-center p-8 bg-muted rounded-lg">
          <h2 className="text-2xl font-semibold mb-2">No Cards Found</h2>
          <p className="mb-4">No cards match your current filters.</p>
          <Button onClick={clearFilters}>Clear Filters</Button>
        </div>
      ) : (
        <>
          <div className={cn("grid", gridClasses[sizeMode])}>
           {filteredCards.map((card) => {
             const isOwned = isInCollection(card.id);
              const isProcessing = processingCards.has(card.id);
              
              return (
                <Card 
                  key={card.id}
                  className={cn(
                    "group overflow-hidden transition-all duration-300 hover:shadow-lg cursor-pointer",
                    "hover:scale-[1.02] relative",
                    isOwned && "ring-2 ring-green-500 ring-offset-2"
                  )}
                  onClick={() => onCardSelect(card)}
                >
                  <div className="relative">
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center z-10">
                      <Button
                        variant={isOwned ? "destructive" : "default"}
                        size="sm"
                        className={cn(
                          "transform translate-y-4 opacity-0 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300",
                          "font-semibold",
                          isProcessing && "pointer-events-none"
                        )}
                        onClick={(e) => isOwned ? handleRemoveFromCollection(card, e) : handleAddToCollection(card, e)}
                        disabled={isProcessing}
                      >
                        {isProcessing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : isOwned ? (
                          <>
                            <Check className="h-4 w-4 mr-2" />
                            Remove
                          </>
                        ) : (
                          <>
                            <Plus className="h-4 w-4 mr-2" />
                            Add
                          </>
                        )}
                      </Button>
                    </div>
                    <img
                      src={card.images.small || fallbackCardImage}
                      alt={card.name}
                      className="w-full aspect-[2.5/3.5] object-contain"
                      loading="lazy"
                      onError={(e) => {
                        if (e.currentTarget.src !== fallbackCardImage) {
                          e.currentTarget.src = fallbackCardImage;
                        } else {
                          e.currentTarget.style.display = 'none';
                        }
                      }}
                    />
                  </div>
                  <CardContent className={cn("p-3", sizeMode === 'small' && "p-2")}>
                     <div className="flex justify-between items-start">
                       <div>
                         <h3 className={cn("font-semibold", sizeMode === 'small' ? "text-xs" : "text-sm")}>{card.name}</h3>
                         {sizeMode === 'medium' && (
                           <p className="text-xs text-muted-foreground">{card.number}/{selectedSet.printedTotal}</p>
                         )}
                       </div>
                     </div>
                    {sizeMode === 'medium' && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {card.rarity && (
                          <Badge variant="outline" className="text-xs">
                            {card.rarity}
                          </Badge>
                        )}
                        {card.types && card.types.map(type => (
                          <Badge key={type} variant="secondary" className="text-xs">
                            {type}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {totalPages > 1 && !hasClientFilters && (
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

      {/* Fixed Stats Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between max-w-7xl">
          <div className="flex gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Owned:</span>
              <Badge className="bg-green-500 hover:bg-green-500">{stats.owned}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Missing:</span>
              <Badge variant="secondary">{stats.missing}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Completion:</span>
              <Badge className="bg-blue-500 hover:bg-blue-500">{stats.percentage.toFixed(1)}%</Badge>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            {stats.total} cards shown
          </div>
        </div>
      </div>
    </div>
  );
};

export default CardGrid;
