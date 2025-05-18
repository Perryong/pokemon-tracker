import React, { useState } from 'react';
import { PokemonCard } from '@/lib/api';
import { useCollection } from '@/lib/collection';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import {
  DollarSign,
  CheckCircle,
  XCircle,
  Star,
  ThumbsUp,
  ShieldAlert,
  AlertCircle,
  Zap,
} from 'lucide-react';

interface CardDetailProps {
  card: PokemonCard | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const CONDITIONS = [
  'Mint',
  'Near Mint',
  'Excellent',
  'Good',
  'Light Played',
  'Played',
  'Poor',
];

const CardDetail: React.FC<CardDetailProps> = ({ card, open, onOpenChange }) => {
  const { 
    isInCollection,
    getCollectionCard,
    addToCollection,
    updateCollectionCard,
    removeFromCollection,
  } = useCollection();
  
  const collectionCard = card ? getCollectionCard(card.id) : null;
  const [quantity, setQuantity] = useState<number>(collectionCard?.quantity || 1);
  const [condition, setCondition] = useState<string>(collectionCard?.condition || 'Near Mint');
  const [purchasePrice, setPurchasePrice] = useState<number>(collectionCard?.purchasePrice || 0);
  const [notes, setNotes] = useState<string>(collectionCard?.notes || '');
  
  const getCardPrice = (card: PokemonCard): { type: string, price: number } | null => {
    if (!card.tcgplayer?.prices) return null;
    
    const prices = card.tcgplayer.prices;
    if (prices.holofoil?.market) return { type: 'Holofoil', price: prices.holofoil.market };
    if (prices.reverseHolofoil?.market) return { type: 'Reverse Holofoil', price: prices.reverseHolofoil.market };
    if (prices.normal?.market) return { type: 'Normal', price: prices.normal.market };
    
    // Fallback to any available market price
    for (const priceType in prices) {
      if (prices[priceType as keyof typeof prices]?.market) {
        return { 
          type: priceType.charAt(0).toUpperCase() + priceType.slice(1), 
          price: prices[priceType as keyof typeof prices]!.market! 
        };
      }
    }
    
    return null;
  };

  const handleAddToCollection = () => {
    if (!card) return;
    
    addToCollection(card, quantity, condition, purchasePrice, notes);
  };

  const handleUpdateCollection = () => {
    if (!card) return;
    
    updateCollectionCard(card.id, {
      quantity,
      condition,
      purchasePrice,
      notes,
    });
  };

  const handleRemoveFromCollection = () => {
    if (!card) return;
    
    removeFromCollection(card.id);
  };

  if (!card) return null;

  const owned = isInCollection(card.id);
  const priceInfo = getCardPrice(card);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            {card.name}
            {owned && (
              <Badge className="ml-2 bg-green-500">In Collection</Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {card.set.name} · {card.number}/{card.set.printedTotal} · {card.rarity}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex justify-center">
            <img 
              src={card.images.large} 
              alt={card.name} 
              className="max-w-full rounded-lg shadow-lg"
            />
          </div>

          <div>
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="info">Card Info</TabsTrigger>
                <TabsTrigger value="market">Market Data</TabsTrigger>
                <TabsTrigger value="collection">Collection</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Type</h3>
                    <div className="flex flex-wrap gap-1">
                      {card.types?.map((type) => (
                        <Badge key={type} variant="secondary">{type}</Badge>
                      )) || "—"}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-1">Subtypes</h3>
                    <div className="flex flex-wrap gap-1">
                      {card.subtypes?.map((subtype) => (
                        <Badge key={subtype} variant="outline">{subtype}</Badge>
                      )) || "—"}
                    </div>
                  </div>
                </div>

                {card.hp && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">HP</h3>
                    <p>{card.hp}</p>
                  </div>
                )}

                {card.attacks && card.attacks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Attacks</h3>
                    <div className="space-y-2">
                      {card.attacks.map((attack, index) => (
                        <Card key={index}>
                          <CardHeader className="py-2 px-3">
                            <CardTitle className="text-sm flex items-center justify-between">
                              <span>{attack.name}</span>
                              <span>{attack.damage}</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="py-2 px-3">
                            <p className="text-xs">{attack.text}</p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {card.weaknesses && card.weaknesses.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Weaknesses</h3>
                    <div className="flex flex-wrap gap-1">
                      {card.weaknesses.map((weakness, index) => (
                        <Badge key={index} variant="destructive">
                          {weakness.type} {weakness.value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {card.resistances && card.resistances.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Resistances</h3>
                    <div className="flex flex-wrap gap-1">
                      {card.resistances.map((resistance, index) => (
                        <Badge key={index} variant="default" className="bg-blue-600">
                          {resistance.type} {resistance.value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {card.retreatCost && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Retreat Cost</h3>
                    <p>{card.retreatCost.length} energy</p>
                  </div>
                )}

                {card.rules && card.rules.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Rules</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {card.rules.map((rule, index) => (
                        <li key={index} className="text-sm">{rule}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-semibold mb-1">Legalities</h3>
                  <div className="flex flex-wrap gap-2">
                    <div className="flex items-center">
                      <span className="text-sm mr-1">Standard:</span>
                      {card.legalities.standard === 'legal' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm mr-1">Expanded:</span>
                      {card.legalities.expanded === 'legal' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm mr-1">Unlimited:</span>
                      {card.legalities.unlimited === 'legal' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                </div>

                {card.artist && (
                  <div>
                    <h3 className="text-sm font-semibold mb-1">Artist</h3>
                    <p>{card.artist}</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="market">
                {card.tcgplayer ? (
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold mb-1">Market Price</h3>
                      {priceInfo ? (
                        <p className="text-2xl font-bold flex items-center">
                          <DollarSign className="h-5 w-5" />
                          {priceInfo.price.toFixed(2)}
                          <span className="text-sm font-normal ml-2">({priceInfo.type})</span>
                        </p>
                      ) : (
                        <p>No price data available</p>
                      )}
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold mb-2">Price Details</h3>
                      <div className="space-y-2">
                        {Object.entries(card.tcgplayer.prices || {}).map(([priceType, priceData]) => (
                          <Card key={priceType}>
                            <CardHeader className="py-2 px-3">
                              <CardTitle className="text-sm">
                                {priceType.charAt(0).toUpperCase() + priceType.slice(1)}
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="py-2 px-3">
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                {priceData?.low !== null && (
                                  <div>
                                    <span className="text-muted-foreground">Low:</span> ${priceData.low?.toFixed(2)}
                                  </div>
                                )}
                                {priceData?.mid !== null && (
                                  <div>
                                    <span className="text-muted-foreground">Mid:</span> ${priceData.mid?.toFixed(2)}
                                  </div>
                                )}
                                {priceData?.high !== null && (
                                  <div>
                                    <span className="text-muted-foreground">High:</span> ${priceData.high?.toFixed(2)}
                                  </div>
                                )}
                                {priceData?.market !== null && (
                                  <div>
                                    <span className="text-muted-foreground">Market:</span> ${priceData.market?.toFixed(2)}
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2">
                      <a 
                        href={card.tcgplayer.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm flex items-center"
                      >
                        View on TCGPlayer
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="text-center p-4">
                    <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p>No market data available for this card</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="collection">
                {owned ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="quantity">Quantity</Label>
                        <Input
                          id="quantity"
                          type="number"
                          min="1"
                          value={quantity}
                          onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="condition">Condition</Label>
                        <Select value={condition} onValueChange={setCondition}>
                          <SelectTrigger id="condition">
                            <SelectValue placeholder="Select condition" />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITIONS.map((cond) => (
                              <SelectItem key={cond} value={cond}>{cond}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="purchasePrice">Purchase Price ($)</Label>
                      <Input
                        id="purchasePrice"
                        type="number"
                        step="0.01"
                        min="0"
                        value={purchasePrice}
                        onChange={(e) => setPurchasePrice(parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="notes">Notes</Label>
                      <Textarea
                        id="notes"
                        placeholder="Add notes about this card..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </div>
                    
                    <div className="flex justify-between pt-2">
                      <Button variant="destructive" onClick={handleRemoveFromCollection}>
                        Remove from Collection
                      </Button>
                      <Button onClick={handleUpdateCollection}>
                        Update
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-center p-4 mb-2">
                      <Star className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                      <p>Add this card to your collection</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="quantity">Quantity</Label>
                        <Input
                          id="quantity"
                          type="number"
                          min="1"
                          value={quantity}
                          onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="condition">Condition</Label>
                        <Select value={condition} onValueChange={setCondition}>
                          <SelectTrigger id="condition">
                            <SelectValue placeholder="Select condition" />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITIONS.map((cond) => (
                              <SelectItem key={cond} value={cond}>{cond}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="purchasePrice">Purchase Price ($)</Label>
                      <Input
                        id="purchasePrice"
                        type="number"
                        step="0.01"
                        min="0"
                        value={purchasePrice}
                        onChange={(e) => setPurchasePrice(parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="notes">Notes</Label>
                      <Textarea
                        id="notes"
                        placeholder="Add notes about this card..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </div>
                    
                    <Button className="w-full" onClick={handleAddToCollection}>
                      Add to Collection
                    </Button>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CardDetail;