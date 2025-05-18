import React, { useState } from "react";
import { useCollection } from "@/lib/collection";
import type { PokemonCard as ApiCard } from "@/lib/api";
import { useCard } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, DollarSign } from "lucide-react";
import CardDetail from "@/components/CardDetail";
import CollectionStats from "@/components/CollectionStats";

/* ---------------- collection-specific type ---------------- */
type CollectionCard = ApiCard & { quantity: number };

const CollectionView: React.FC = () => {
  /* ---------------- data from store ---------------- */
  const { getCollectionCards } = useCollection();
  const collectionCards = getCollectionCards() as CollectionCard[];

  /* ---------------- component state ---------------- */
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [selectedRarity, setSelectedRarity] = useState<string | null>(null);
  const [selectedSet, setSelectedSet] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [showCardDetail, setShowCardDetail] = useState(false);

  const { card: selectedCard } = useCard(selectedCardId ?? "");

  /* ---------------- filter helpers ---------------- */
  const uniqueRarities = Array.from(
    new Set(
      collectionCards
        .map((c) => c.rarity)
        .filter((r): r is string => !!r) // type-guard
    )
  );

  const uniqueSets = Array.from(
    new Set(collectionCards.map((c) => c.set.name))
  );

  const uniqueTypes = Array.from(
    new Set(collectionCards.flatMap((c) => c.types ?? []))
  );

  /* ---------------- filtering ---------------- */
  const filteredCards = collectionCards.filter((card) => {
    const matchesSearch =
      searchQuery === "" ||
      card.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      card.number.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRarity = !selectedRarity || card.rarity === selectedRarity;
    const matchesSet = !selectedSet || card.set.name === selectedSet;
    const matchesType =
      !selectedType || (card.types && card.types.includes(selectedType));

    return matchesSearch && matchesRarity && matchesSet && matchesType;
  });

  /* ---------------- sorting ---------------- */
  const sortedCards = [...filteredCards].sort((a, b) => {
    switch (sortBy) {
      case "name":
        return a.name.localeCompare(b.name);
      case "set":
        return a.set.name.localeCompare(b.set.name);
      case "number":
        return (
          a.set.name.localeCompare(b.set.name) ||
          a.number.localeCompare(b.number, undefined, { numeric: true })
        );
      case "rarity":
        return (a.rarity ?? "").localeCompare(b.rarity ?? "");
      case "price-high":
        return getCardPrice(b) - getCardPrice(a);
      case "price-low":
        return getCardPrice(a) - getCardPrice(b);
      default:
        return 0;
    }
  });

  /* ---------------- util: best price ---------------- */
  const getCardPrice = (card: CollectionCard): number => {
    const prices = card.tcgplayer?.prices;
    if (!prices) return 0;

    return (
      prices.holofoil?.market ??
      prices.reverseHolofoil?.market ??
      prices.normal?.market ??
      Object.values(prices).find((p) => p?.market)?.market ??
      0
    );
  };

  /* ---------------- handlers ---------------- */
  const handleCardSelect = (card: CollectionCard) => {
    setSelectedCardId(card.id);
    setShowCardDetail(true);
  };

  const clearFilters = () => {
    setSearchQuery("");
    setSelectedRarity(null);
    setSelectedSet(null);
    setSelectedType(null);
  };

  /* ---------------- render ---------------- */
  return (
    <div className="container mx-auto p-4">
      <Tabs defaultValue="cards" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="cards">My Cards</TabsTrigger>
          <TabsTrigger value="stats">Collection Stats</TabsTrigger>
        </TabsList>

        {/* ---------------- CARDS TAB ---------------- */}
        <TabsContent value="cards">
          <div className="space-y-4">
            {/* search + sort */}
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
                  <SelectItem value="price-high">Price (High→Low)</SelectItem>
                  <SelectItem value="price-low">Price (Low→High)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {/* rarity */}
              <Select
                value={selectedRarity ?? "none"}
                onValueChange={(v) => setSelectedRarity(v === "none" ? null : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Rarity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Rarities</SelectItem>
                  {uniqueRarities.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* set */}
              <Select
                value={selectedSet ?? "none"}
                onValueChange={(v) => setSelectedSet(v === "none" ? null : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Set" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Sets</SelectItem>
                  {uniqueSets.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* type */}
              <Select
                value={selectedType ?? "none"}
                onValueChange={(v) => setSelectedType(v === "none" ? null : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter by Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">All Types</SelectItem>
                  {uniqueTypes.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* grid / empty states */}
            {collectionCards.length === 0 ? (
              <EmptyState
                heading="Your Collection is Empty"
                sub="Start adding cards to build your collection!"
              />
            ) : sortedCards.length === 0 ? (
              <EmptyState
                heading="No Cards Found"
                sub="No cards match your current filters."
                ctaLabel="Clear Filters"
                onCta={clearFilters}
              />
            ) : (
              <CardGrid cards={sortedCards} onSelect={handleCardSelect} />
            )}
          </div>
        </TabsContent>

        {/* ---------------- STATS TAB ---------------- */}
        <TabsContent value="stats">
          <CollectionStats />
        </TabsContent>
      </Tabs>

      {/* card modal */}
      <CardDetail
        card={selectedCard}
        open={showCardDetail}
        onOpenChange={setShowCardDetail}
      />
    </div>
  );
};

/* ---------------- helpers ---------------- */

const EmptyState: React.FC<{
  heading: string;
  sub: string;
  ctaLabel?: string;
  onCta?: () => void;
}> = ({ heading, sub, ctaLabel, onCta }) => (
  <div className="text-center p-8 mt-4">
    <h2 className="text-xl font-bold mb-4">{heading}</h2>
    <p className="mb-4 text-muted-foreground">{sub}</p>
    {ctaLabel && (
      <Button onClick={onCta} variant="default">
        {ctaLabel}
      </Button>
    )}
  </div>
);

const CardGrid: React.FC<{
  cards: CollectionCard[];
  onSelect: (c: CollectionCard) => void;
}> = ({ cards, onSelect }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mt-4">
    {cards.map((card) => {
      const price =
        card.tcgplayer?.prices?.holofoil?.market ??
        card.tcgplayer?.prices?.reverseHolofoil?.market ??
        card.tcgplayer?.prices?.normal?.market ??
        0;

      return (
        <Card
          key={card.id}
          className="overflow-hidden hover:shadow-lg cursor-pointer transition-all hover:scale-[1.02]"
          onClick={() => onSelect(card)}
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
                <p className="text-xs text-muted-foreground">
                  {card.set.name} · {card.number}
                </p>
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
              {card.types?.map((t) => (
                <Badge key={t} variant="secondary" className="text-xs">
                  {t}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      );
    })}
  </div>
);

export default CollectionView;
