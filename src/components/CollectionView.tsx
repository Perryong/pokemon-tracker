import React, { useState } from 'react';
import { useCollection } from '@/lib/collection';
import { PokemonCard, useCard } from '@/lib/api';
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
  Card, 
  CardContent,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, Filter, DollarSign } from 'lucide-react';
import CardDetail from '@/components/CardDetail';
import CollectionStats from '@/components/CollectionStats';

const CollectionView: React.FC = () => {
  const { getCollectionCards } = useCollection();
  const collectionCards = getCollectionCards();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [selectedRarity, setSelectedRarity] = useState<string | null>(null);
  const [selectedSet, setSelectedSet] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [showCardDetail, setShowCardDetail] = useState(false);
  
  const { card: selectedCard } = useCard(selectedCardId);
  
  // Get unique rarities, sets, and types for filters
  const uniqueRarities = Array.from(new Set(collectionCards.map(card => card.rarity).filter(Boolean)));
  const uniqueSets = Array.from(new Set(collectionCards.map(card => card.set.name)));
  const uniqueTypes = Array.from(new Set(collectionCards.flatMap(card => card.types || [])));
  
  // Filter cards based on search and filters
  const filteredCards = collectionCards.filter(card => {
    const matchesSearch = searchQuery === '' || 
      card.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.number.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesRarity = !selectedRarity || card.rarity === selectedRarity;
    const matchesSet = !selectedSet || card.set.name === selectedSet;
    const matchesType = !selectedType || (card.types && card.types.includes(selectedType));
    
    return matchesSearch && matchesRarity && matchesSet && matchesType;
  });
  
  // Sort cards
  const sortedCards = [...filteredCards].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'set':
        return a.set.name.localeCompare(b.set.name);
      case 'number':
        return a.set.name.localeCompare(b.set.name) || 
               a.number.localeCompare(b.number, undefined, { numeric: true });
      case 'rarity':
        return (a.rarity || '').localeCompare(b.rarity || '');
      case 'price-high':
        return getCardPrice(b) - getCardPrice(a);
      case 'price-low':
        return getCardPrice(a) - getCardPrice(b);
      default:
        return 0;
    }
  });
  
  // Function to get the best available price for a card
  const getCardPrice = (card: PokemonCard): number => {
    if (!card.tcgplayer?.prices) return 0;
    
    const prices = card.tcgplayer.prices;
    if (prices.holofoil?.market) return prices.holofoil.market;
    if (prices.reverseHolofoil?.market) return prices.reverseHolofoil.market;
    if (prices.normal?.market) return prices.normal.market;
    
    // Fallback to any available market price
    for (const priceType in prices) {
      if (prices[priceType as keyof typeof prices]?.market) {
        return prices[priceType as keyof typeof prices]!.market!;
      }
    }
    
    return 0;
  };
  
  const handleCardSelect = (card: PokemonCard) => {
    setSelectedCardId(card.id);
    setShowCardDetail(true);
  };
  
  const clearFilters = () => {
    setSearchQuery('');
    setSelectedRarity(null);
    setSelectedSet(null);
    setSelectedType(null);
  };

  return (
    <div className="container mx-auto p-4">
      <Tabs defaultValue="cards" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="cards">My Cards</TabsTrigger>
          <TabsTrigger value="stats">Collection Stats</TabsTrigger>
        </TabsList>
        
        <TabsContent value="cards">
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name or number..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
              
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name (A-Z)</SelectItem>
                  <SelectItem value="set">Set (A-Z)</SelectItem>
                  <SelectItem value="number">Set & Number</SelectItem>
                  <SelectItem value="rarity">Rarity</SelectItem>
                  <SelectItem value="price-high">Price (High-Low)</SelectItem>
                  <SelectItem value="price-low">Price (Low-High)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <Select value={selectedRarity || "none"} onValueChange={(value) => setSelectedRarity(value === "none" ? null : value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Rarity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Rarities</SelectItem>
                  {uniqueRarities.map(rarity => (
                    <SelectItem key={rarity} value={rarity}>{rarity}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={selectedSet || "none"} onValueChange={(value) => setSelectedSet(value === "none" ? null : value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Set" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Sets</SelectItem>
                  {uniqueSets.map(set => (
                    <SelectItem key={set} value={set}>{set}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={selectedType || "none"} onValueChange={(value) => setSelectedType(value === "none" ? null : value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Types</SelectItem>
                  {uniqueTypes.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {collectionCards.length === 0 ? (
              <div className="text-center p-8 mt-4">
                <h2 className="text-2xl font-bold mb-4">Your Collection is Empty</h2>
                <p className="mb-6 text-muted-foreground">
                  Start adding cards to build your collection!
                </p>
              </div>
            ) : sortedCards.length === 0 ? (
              <div className="text-center p-8 mt-4">
                <h2 className="text-xl font-bold mb-4">No Cards Found</h2>
                <p className="mb-4 text-muted-foreground">
                  No cards match your current filters.
                </p>
                <Button onClick={clearFilters}>Clear Filters</Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mt-4">
                {sortedCards.map((card) => {
                  const price = getCardPrice(card);
                  
                  return (
                    <Card 
                      key={card.id}
                      className="overflow-hidden hover:shadow-lg cursor-pointer transition-all hover:scale-[1.02]"
                      onClick={() => handleCardSelect(card)}
                    >
                      <div className="relative pt-[139.4%]">
                        <img
                          src={card.images.small}
                          alt={card.name}
                          className="absolute top-0 left-0 w-full h-full object-contain"
                          loading="lazy"
                        />
                        <div className="absolute top-2 right-2 bg-green-500 text-white rounded-full h-6 w-6 flex items-center justify-center text-xs font-bold">
                          {card.quantity}
                        </div>
                      </div>
                      <CardContent className="p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-semibold text-sm">{card.name}</h3>
                            <p className="text-xs text-muted-foreground">{card.set.name} · {card.number}</p>
                          </div>
                          {price > 0 && (
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
            )}
          </div>
        </TabsContent>
        
        <TabsContent value="stats">
          <CollectionStats />
        </TabsContent>
      </Tabs>
      
      <CardDetail 
        card={selectedCard} 
        open={showCardDetail} 
        onOpenChange={setShowCardDetail} 
      />
    </div>
  );
};

export default CollectionView;