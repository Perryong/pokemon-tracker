import React, { useMemo } from "react";
import { useCollection } from "@/lib/collection";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

const CollectionView: React.FC = () => {
  const { cardQuantities } = useCollection();
  
  // Calculate stats - unique cards vs total quantity
  const stats = useMemo(() => {
    const uniqueCards = Object.keys(cardQuantities).length;
    const totalQuantity = Object.values(cardQuantities).reduce((sum, qty) => sum + qty, 0);
    return { uniqueCards, totalQuantity };
  }, [cardQuantities]);
  
  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6">My Collection</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Collection View</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Unique Cards</p>
                <p className="text-3xl font-bold">{stats.uniqueCards}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Quantity</p>
                <p className="text-3xl font-bold">{stats.totalQuantity}</p>
                {stats.totalQuantity > stats.uniqueCards && (
                  <p className="text-xs text-muted-foreground mt-1">
                    ({stats.totalQuantity - stats.uniqueCards} duplicates)
                  </p>
                )}
              </div>
            </div>
            
            <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <AlertCircle className="h-6 w-6 mx-auto mb-2 text-blue-600" />
              <p className="text-center text-blue-700">
                Collection view with cards display, filtering, and sorting coming in v2
              </p>
              <p className="text-center text-sm text-blue-600 mt-2">
                For now, use the Sets view to browse and add cards to your collection
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CollectionView;
