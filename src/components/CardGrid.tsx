import React, { useState } from 'react';
import { PokemonCard, PokemonSet, useCards } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ChevronDown, DollarSign, Filter } from 'lucide-react';
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
} from '@/components/ui/pagination';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Slider } from '@/components/ui/slider';
import { cn } from '@/lib/utils';

interface CardGridProps {
  selectedSet: PokemonSet;
  onBackClick: () => void;
  onCardSelect: (card: PokemonCard) => void;
}

const CardGrid: React.FC<CardGridProps> = ({ selectedSet, onBackClick, onCardSelect }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [subtypeFilter, setSubtypeFilter] = useState<string>('');
  const [rarityFilter, setRarityFilter] = useState<string>('');
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 1000]);
  const [showFilters, setShowFilters] = useState(false);
  const pageSize = 20;

  const { isInCollection } = useCollection();

  // Build filters for the API request
  const filters: Record<string, string> = {};
  if (typeFilter) filters['types'] = typeFilter;
  if (subtypeFilter) filters['subtypes'] = subtypeFilter;
  if (rarityFilter) filters['rarity'] = rarityFilter;

  // We can't filter by price range in the API directly, so we'll fetch and filter client-side
  const { cards, totalCards, loading, error } = useCards(selectedSet.id, currentPage, pageSize, filters);

  // Filter cards by price range client-side
  const filteredCards = cards.filter(card => {
    if (!card.tcgplayer?.prices) return true; // Include cards without price data

    // Check if any price falls within range
    for (const priceType in card.tcgplayer.prices) {
      const price = card.tcgplayer.prices[priceType as keyof typeof card.tcgplayer.prices];
      if (price?.market && price.market >= priceRange[0] && price.market <= priceRange[1]) {
        return true;
      }
    }
    return false;
  });

  const totalPages = Math.ceil(totalCards / pageSize);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo(0, 0);
  };

  const clearFilters = () => {
    setTypeFilter('');
    setSubtypeFilter('');
    setRarityFilter('');
    setPriceRange([0, 1000]);
  };

  // Get unique card types, subtypes, and rarities from current cards
  const uniqueTypes = Array.from(new Set(cards.flatMap(card => card.types || [])));
  const uniqueSubtypes = Array.from(new Set(cards.flatMap(card => card.subtypes || [])));
  const uniqueRarities = Array.from(new Set(cards.map(card => card.rarity).filter(Boolean) as string[]));

  // Function to get the best available price for a card
  const getCardPrice = (card: PokemonCard): number | null => {
    if (!card.tcgplayer?.prices) return null;
    
    const prices = card.tcgplayer.prices;
    if (prices.holofoil?.market) return prices.holofoil.market;
    if (prices.reverseHolofoil?.market) return prices.reverseHolofoil.market;
    if (prices.normal?.market) return prices.normal.market;
    
    // Fallback to any available market price
    for (const priceType in prices) {
      if (prices[priceType as keyof typeof prices]?.market) {
        return prices[priceType as keyof typeof prices]!.market;
      }
    }
    
    return null;
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
    <div className="container mx-auto p-4">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="icon" onClick={onBackClick}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            {selectedSet.name}
            <img 
              src={selectedSet.images.symbol} 
              alt={`${selectedSet.name} symbol`} 
              className="h-6 w-6"
            />
          </h1>
          <p className="text-sm text-muted-foreground">
            {selectedSet.total} cards in this set
          </p>
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
                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Types</SelectItem>
                        {uniqueTypes.map(type => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Select value={subtypeFilter} onValueChange={setSubtypeFilter}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Subtype" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Subtypes</SelectItem>
                        {uniqueSubtypes.map(subtype => (
                          <SelectItem key={subtype} value={subtype}>{subtype}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Select value={rarityFilter} onValueChange={setRarityFilter}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Rarity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Rarities</SelectItem>
                        {uniqueRarities.map(rarity => (
                          <SelectItem key={rarity} value={rarity}>{rarity}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </AccordionContent>
              </AccordionItem>
              
              <AccordionItem value="price-range">
                <AccordionTrigger>Price Range</AccordionTrigger>
                <AccordionContent>
                  <div className="mb-2">
                    <Slider
                      min={0}
                      max={1000}
                      step={1}
                      value={priceRange}
                      onValueChange={(value) => setPriceRange(value as [number, number])}
                      className="mb-6"
                    />
                    <div className="flex justify-between text-sm">
                      <span>${priceRange[0].toFixed(2)}</span>
                      <span>${priceRange[1].toFixed(2)}</span>
                    </div>
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

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {Array.from({ length: 20 }).map((_, index) => (
            <Card key={index}>
              <CardContent className="p-3">
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
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredCards.map((card) => {
              const price = getCardPrice(card);
              const isOwned = isInCollection(card.id);
              
              return (
                <Card 
                  key={card.id}
                  className={cn(
                    "overflow-hidden transition-all hover:shadow-lg cursor-pointer",
                    "hover:scale-[1.02] relative",
                    isOwned && "ring-2 ring-green-500 ring-offset-2"
                  )}
                  onClick={() => onCardSelect(card)}
                >
                  {isOwned && (
                    <div className="absolute top-2 right-2 z-10">
                      <Badge className="bg-green-500">Owned</Badge>
                    </div>
                  )}
                  <div className="relative pt-[139.4%]"> {/* Aspect ratio for Pokémon cards */}
                    <img
                      src={card.images.small}
                      alt={card.name}
                      className="absolute top-0 left-0 w-full h-full object-contain"
                      loading="lazy"
                    />
                  </div>
                  <CardContent className="p-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-sm">{card.name}</h3>
                        <p className="text-xs text-muted-foreground">{card.number}/{selectedSet.printedTotal}</p>
                      </div>
                      {price && (
                        <div className="flex items-center text-sm font-medium">
                          <DollarSign className="h-3 w-3 mr-1" />
                          {price.toFixed(2)}
                        </div>
                      )}
                    </div>
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
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {totalPages > 1 && (
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

export default CardGrid;