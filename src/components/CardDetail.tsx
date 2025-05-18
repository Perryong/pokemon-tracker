/* --- src/components/CardDetail.tsx ---------------------------------------- */

import React, { useState } from "react";
import { PokemonCard } from "@/lib/api";
import { useCollection } from "@/lib/collection";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DollarSign,
  Star,
  AlertCircle,
} from "lucide-react";

/* ------------------------------------------------------------------ */

interface CardDetailProps {
  card: PokemonCard | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const CONDITIONS = [
  "Mint",
  "Near Mint",
  "Excellent",
  "Good",
  "Light Played",
  "Played",
  "Poor",
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
  const [quantity, setQuantity] = useState<number>(collectionCard?.quantity ?? 1);
  const [condition, setCondition] = useState<string>(
    collectionCard?.condition ?? "Near Mint",
  );
  const [purchasePrice, setPurchasePrice] = useState<number>(
    collectionCard?.purchasePrice ?? 0,
  );
  const [notes, setNotes] = useState<string>(collectionCard?.notes ?? "");

  /* ------------------- helpers ------------------- */

  const getCardPrice = (
    c: PokemonCard,
  ): { type: string; price: number } | null => {
    const prices = c.tcgplayer?.prices;
    if (!prices) return null;

    if (prices.holofoil?.market != null)
      return { type: "Holofoil", price: Number(prices.holofoil.market) };
    if (prices.reverseHolofoil?.market != null)
      return {
        type: "Reverse Holofoil",
        price: Number(prices.reverseHolofoil.market),
      };
    if (prices.normal?.market != null)
      return { type: "Normal", price: Number(prices.normal.market) };

    for (const [k, p] of Object.entries(prices)) {
      if (p?.market != null) {
        return { type: k.charAt(0).toUpperCase() + k.slice(1), price: Number(p.market) };
      }
    }
    return null;
  };

  /* ------------------- actions ------------------- */

  const handleAddToCollection = () =>
    card &&
    addToCollection(card, quantity, condition, purchasePrice, notes);

  const handleUpdateCollection = () =>
    card &&
    updateCollectionCard(card.id, { quantity, condition, purchasePrice, notes });

  const handleRemoveFromCollection = () => card && removeFromCollection(card.id);

  /* ------------------- render guard ------------------- */

  if (!card) return null;

  const owned = isInCollection(card.id);
  const priceInfo = getCardPrice(card);

  /* ------------------------------------------------------------------ */

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            {card.name}
            {owned && <Badge className="ml-2 bg-green-500">In Collection</Badge>}
          </DialogTitle>
          <DialogDescription>
            {card.set.name} · {card.number}/{card.set.printedTotal} · {card.rarity}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* ---------------- image ---------------- */}
          <div className="flex justify-center">
            <img
              src={card.images.large}
              alt={card.name}
              className="max-w-full rounded-lg shadow-lg"
            />
          </div>

          {/* ---------------- tabs ---------------- */}
          <div>
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="info">Card Info</TabsTrigger>
                <TabsTrigger value="market">Market Data</TabsTrigger>
                <TabsTrigger value="collection">Collection</TabsTrigger>
              </TabsList>

              {/* ========== INFO TAB (unchanged) ========== */}
              {/* keep all your existing “info” tab markup here */}

              {/* ========== MARKET TAB ========== */}
              <TabsContent value="market">
                {card.tcgplayer ? (
                  <div className="space-y-4">
                    {/* headline price */}
                    <div>
                      <h3 className="text-sm font-semibold mb-1">Market Price</h3>
                      {priceInfo ? (
                        <p className="text-2xl font-bold flex items-center">
                          <DollarSign className="h-5 w-5" />
                          {priceInfo.price.toFixed(2)}
                          <span className="text-sm font-normal ml-2">
                            ({priceInfo.type})
                          </span>
                        </p>
                      ) : (
                        <p>No price data available</p>
                      )}
                    </div>

                    {/* price breakdown */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Price Details</h3>
                      <div className="space-y-2">
                        {Object.entries(card.tcgplayer.prices ?? {})
                          .filter(([, p]) => p != null)
                          .map(([priceType, priceData]) => {
                            const data = priceData!; // now definitely defined
                            return (
                              <Card key={priceType}>
                                <CardHeader className="py-2 px-3">
                                  <CardTitle className="text-sm">
                                    {priceType.charAt(0).toUpperCase() +
                                      priceType.slice(1)}
                                  </CardTitle>
                                </CardHeader>
                                <CardContent className="py-2 px-3">
                                  <div className="grid grid-cols-2 gap-2 text-sm">
                                    {data.low != null && (
                                      <div>
                                        <span className="text-muted-foreground">
                                          Low:
                                        </span>{" "}
                                        ${data.low.toFixed(2)}
                                      </div>
                                    )}
                                    {data.mid != null && (
                                      <div>
                                        <span className="text-muted-foreground">
                                          Mid:
                                        </span>{" "}
                                        ${data.mid.toFixed(2)}
                                      </div>
                                    )}
                                    {data.high != null && (
                                      <div>
                                        <span className="text-muted-foreground">
                                          High:
                                        </span>{" "}
                                        ${data.high.toFixed(2)}
                                      </div>
                                    )}
                                    {data.market != null && (
                                      <div>
                                        <span className="text-muted-foreground">
                                          Market:
                                        </span>{" "}
                                        ${data.market.toFixed(2)}
                                      </div>
                                    )}
                                  </div>
                                </CardContent>
                              </Card>
                            );
                          })}
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

              {/* ========== COLLECTION TAB ========== */}
              <TabsContent value="collection">
                {owned ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="quantity">Quantity</Label>
                        <Input
                          id="quantity"
                          type="number"
                          min={1}
                          value={quantity}
                          onChange={(e) =>
                            setQuantity(parseInt(e.target.value) || 1)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="condition">Condition</Label>
                        <Select value={condition} onValueChange={setCondition}>
                          <SelectTrigger id="condition">
                            <SelectValue placeholder="Select condition" />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITIONS.map((c) => (
                              <SelectItem key={c} value={c}>
                                {c}
                              </SelectItem>
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
                        min={0}
                        value={purchasePrice}
                        onChange={(e) =>
                          setPurchasePrice(parseFloat(e.target.value) || 0)
                        }
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
                      <Button onClick={handleUpdateCollection}>Update</Button>
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
                          min={1}
                          value={quantity}
                          onChange={(e) =>
                            setQuantity(parseInt(e.target.value) || 1)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="condition">Condition</Label>
                        <Select value={condition} onValueChange={setCondition}>
                          <SelectTrigger id="condition">
                            <SelectValue placeholder="Select condition" />
                          </SelectTrigger>
                          <SelectContent>
                            {CONDITIONS.map((c) => (
                              <SelectItem key={c} value={c}>
                                {c}
                              </SelectItem>
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
                        min={0}
                        value={purchasePrice}
                        onChange={(e) =>
                          setPurchasePrice(parseFloat(e.target.value) || 0)
                        }
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
