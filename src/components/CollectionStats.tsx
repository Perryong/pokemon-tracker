import React from 'react';
import { useCollection } from '@/lib/collection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { DollarSign, CreditCard, Star, Layers } from 'lucide-react';

const CollectionStats: React.FC = () => {
  const { getCollectionCards, calculateCollectionValue } = useCollection();
  const collectionCards = getCollectionCards();
  const collectionValue = calculateCollectionValue();
  
  // Calculate stats
  const totalCards = collectionCards.length;
  const totalQuantity = collectionCards.reduce((total, card) => total + card.quantity, 0);
  
  // Count cards by rarity
  const rarityCount = collectionCards.reduce((counts, card) => {
    const rarity = card.rarity || 'Unknown';
    counts[rarity] = (counts[rarity] || 0) + card.quantity;
    return counts;
  }, {} as Record<string, number>);
  
  const rarityData = Object.entries(rarityCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
  
  // Count cards by set
  const setCount = collectionCards.reduce((counts, card) => {
    const setName = card.set.name;
    counts[setName] = (counts[setName] || 0) + card.quantity;
    return counts;
  }, {} as Record<string, number>);
  
  const setData = Object.entries(setCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5); // Top 5 sets
  
  // Count cards by type
  const typeCount = collectionCards.reduce((counts, card) => {
    const types = card.types || ['Colorless'];
    types.forEach(type => {
      counts[type] = (counts[type] || 0) + card.quantity;
    });
    return counts;
  }, {} as Record<string, number>);
  
  const typeData = Object.entries(typeCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
  
  // Most valuable cards
  const valuableCards = [...collectionCards]
    .filter(card => {
      if (!card.tcgplayer?.prices) return false;
      
      // Find the highest market price for this card
      let highestPrice = 0;
      for (const priceType in card.tcgplayer.prices) {
        const price = card.tcgplayer.prices[priceType as keyof typeof card.tcgplayer.prices];
        if (price?.market && price.market > highestPrice) {
          highestPrice = price.market;
        }
      }
      
      return highestPrice > 0;
    })
    .sort((a, b) => {
      // Get highest market price for card a
      let priceA = 0;
      if (a.tcgplayer?.prices) {
        for (const priceType in a.tcgplayer.prices) {
          const price = a.tcgplayer.prices[priceType as keyof typeof a.tcgplayer.prices];
          if (price?.market && price.market > priceA) {
            priceA = price.market;
          }
        }
      }
      
      // Get highest market price for card b
      let priceB = 0;
      if (b.tcgplayer?.prices) {
        for (const priceType in b.tcgplayer.prices) {
          const price = b.tcgplayer.prices[priceType as keyof typeof b.tcgplayer.prices];
          if (price?.market && price.market > priceB) {
            priceB = price.market;
          }
        }
      }
      
      return priceB - priceA;
    })
    .slice(0, 5); // Top 5 most valuable cards
  
  // Colors for pie chart
  const COLORS = ['#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2', '#073B4C', '#8338EC', '#3A86FF'];
  
  if (totalCards === 0) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold mb-4">Your Collection is Empty</h2>
        <p className="mb-6 text-muted-foreground">
          Browse the card sets and start adding cards to your collection!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collection Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${collectionValue.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">Based on current market prices</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Cards</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCards}</div>
            <p className="text-xs text-muted-foreground">Different cards in collection</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cards</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalQuantity}</div>
            <p className="text-xs text-muted-foreground">Including duplicates</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sets</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(setCount).length}</div>
            <p className="text-xs text-muted-foreground">Different sets in collection</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="distribution" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
          <TabsTrigger value="valuable">Most Valuable</TabsTrigger>
          <TabsTrigger value="sets">Set Breakdown</TabsTrigger>
        </TabsList>
        
        <TabsContent value="distribution" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cards by Rarity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={rarityData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {rarityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value) => [`${value} cards`, 'Quantity']}
                        labelFormatter={(label) => `Rarity: ${label}`}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cards by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={typeData}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 50, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="name" />
                      <Tooltip />
                      <Bar dataKey="value" fill="hsl(var(--chart-1))" name="Cards" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="valuable">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Most Valuable Cards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {valuableCards.length > 0 ? (
                  valuableCards.map((card) => {
                    // Find the highest market price for this card
                    let highestPrice = 0;
                    let priceType = '';
                    
                    if (card.tcgplayer?.prices) {
                      for (const type in card.tcgplayer.prices) {
                        const price = card.tcgplayer.prices[type as keyof typeof card.tcgplayer.prices];
                        if (price?.market && price.market > highestPrice) {
                          highestPrice = price.market;
                          priceType = type;
                        }
                      }
                    }
                    
                    return (
                      <div key={card.id} className="flex items-center space-x-4">
                        <div className="w-16 h-22 shrink-0">
                          <img 
                            src={card.images.small} 
                            alt={card.name} 
                            className="w-full h-auto object-contain"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{card.name}</p>
                          <p className="text-sm text-muted-foreground truncate">
                            {card.set.name} · {card.number}/{card.set.printedTotal}
                          </p>
                          <div className="flex items-center mt-1">
                            <Badge variant="outline" className="mr-2">
                              {card.rarity}
                            </Badge>
                            <Badge variant="secondary">
                              Qty: {card.quantity}
                            </Badge>
                          </div>
                        </div>
                        <div className="font-bold text-lg flex items-center">
                          <DollarSign className="h-4 w-4 mr-1" />
                          {highestPrice.toFixed(2)}
                          <span className="text-xs font-normal ml-1">({priceType})</span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-center py-4 text-muted-foreground">
                    No price data available for your collection
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="sets">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Top Sets in Collection</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={setData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 75 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={70}
                      interval={0}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="hsl(var(--chart-2))" name="Cards" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4">
                <h3 className="font-medium mb-2">All Sets ({Object.keys(setCount).length})</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(setCount)
                    .sort((a, b) => b[1] - a[1])
                    .map(([setName, count]) => (
                      <Badge key={setName} variant="outline" className="py-1">
                        {setName}: {count}
                      </Badge>
                    ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CollectionStats;