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
  CardDescription,
  CardFooter,
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
  CheckCircle,
  XCircle,
  Star,
  ThumbsUp,
  AlertCircle,
} from "lucide-react";      // ← ShieldAlert & Zap removed

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
    card: PokemonCard,
  ): { type: string; price: number } | null => {
    const prices = card.tcgplayer?.prices;
    if (!prices) return null;

    if (prices.holofoil?.market)
      return { type: "Holofoil", price: prices.holofoil.market };
    if (prices.reverseHolofoil?.market)
      return { type: "Reverse Holofoil", price: prices.reverseHolofoil.market };
    if (prices.normal?.market)
      return { type: "Normal", price: prices.normal.market };

    // fallback to the first price that has market data
    for (const [key, p] of Object.entries(prices)) {
      if (p?.market !== undefined) {
        return {
          type: key.charAt(0).toUpperCase() + key.slice(1),
          price: p.market,
        };
      }
    }
    return null;
  };

  /* ------------------- actions ------------------- */

  const handleAddToCollection = () => {
    if (!card) return;
    addToCollection(card, quantity, condition, purchasePrice, notes);
  };

  const handleUpdateCollection = () => {
    if (!card) return;
    updateCollectionCard(card.id, { quantity, condition, purchasePrice, notes });
  };

  const handleRemoveFromCollection = () => {
    if (!card) return;
    removeFromCollection(card.id);
  };

  /* ------------------- render guards ------------------- */

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
            {card.set.name} · {card.number}/{card.set.printedTotal} ·{" "}
            {card.rarity}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* ------------- left side: image ------------- */}
          <div className="flex justify-center">
            <img
              src={card.images.large}
              alt={card.name}
              className="max-w-full rounded-lg shadow-lg"
            />
          </div>

          {/* ------------- right side: tabs ------------- */}
          <div>
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="info">Card Info</TabsTrigger>
                <TabsTrigger value="market">Market Data</TabsTrigger>
                <TabsTrigger value="collection">Collection</TabsTrigger>
              </TabsList>

              {/* =============== TAB – INFO =============== */}
              <TabsContent value="info" className="space-y-4">
                {/* … (unchanged content clipped for brevity) … */}

                <div>
                  <h3 className="text-sm font-semibold mb-1">Legalities</h3>
                  {card.legalities ? (
                    <div className="flex flex-wrap gap-2">
                      {(["standard", "expanded", "unlimited"] as const).map(
                        (fmt) => (
                          <div key={fmt} className="flex items-center">
                            <span className="text-sm mr-1">
                              {fmt.charAt(0).toUpperCase() + fmt.slice(1)}:
                            </span>
                            {card.legalities?.[fmt] === "legal" ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">—</p>
                  )}
                </div>

                {/* … remainder unchanged … */}
              </TabsContent>

              {/* ============ TAB – MARKET DATA ============ */}
              <TabsContent value="market">
                {card.tcgplayer ? (
                  <div className="space-y-4">
                    {/* Market price */}
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

                    {/* Price breakdown */}
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Price Details</h3>
                      <div className="space-y-2">
                        {Object.entries(card.tcgplayer.prices ?? {})
                          .filter(([, p]): p is NonNullable<typeof p> => !!p) // ← narrow undefined out
                          .map(([priceType, priceData]) => (
                            <Card key={priceType}>
                              <CardHeader className="py-2 px-3">
                                <CardTitle className="text-sm">
                                  {priceType.charAt(0).toUpperCase() +
                                    priceType.slice(1)}
                                </CardTitle>
                              </CardHeader>
                              <CardContent className="py-2 px-3">
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                  {priceData.low != null && (
                                    <div>
                                      <span className="text-muted-foreground">
                                        Low:
                                      </span>{" "}
                                      ${priceData.low.toFixed(2)}
                                    </div>
                                  )}
                                  {priceData.mid != null && (
                                    <div>
                                      <span className="text-muted-foreground">
                                        Mid:
                                      </span>{" "}
                                      ${priceData.mid.toFixed(2)}
                                    </div>
                                  )}
                                  {priceData.high != null && (
                                    <div>
                                      <span className="text-muted-foreground">
                                        High:
                                      </span>{" "}
                                      ${priceData.high.toFixed(2)}
                                    </div>
                                  )}
                                  {priceData.market != null && (
                                    <div>
                                      <span className="text-muted-foreground">
                                        Market:
                                      </span>{" "}
                                      ${priceData.market.toFixed(2)}
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

              {/* ========= TAB – COLLECTION (unchanged) ========= */}
              {/* … keep your existing “collection” tab code … */}
            </Tabs>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CardDetail;
