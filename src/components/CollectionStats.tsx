import React, { useMemo } from 'react';
import { useCollection } from '@/lib/collection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

const CollectionStats: React.FC = () => {
  const { cardQuantities } = useCollection();
  
  const stats = useMemo(() => {
    const uniqueCards = Object.keys(cardQuantities).length;
    const totalQuantity = Object.values(cardQuantities).reduce((sum, qty) => sum + qty, 0);
    const duplicates = totalQuantity - uniqueCards;
    
    // Count cards by quantity range
    const singleCopies = Object.values(cardQuantities).filter(q => q === 1).length;
    const withDuplicates = Object.values(cardQuantities).filter(q => q > 1).length;
    
    return { uniqueCards, totalQuantity, duplicates, singleCopies, withDuplicates };
  }, [cardQuantities]);
  
  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <h1 className="text-3xl font-bold mb-6">Collection Statistics</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Basic Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">Unique Cards</p>
              <p className="text-2xl font-bold">{stats.uniqueCards}</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">Total Quantity</p>
              <p className="text-2xl font-bold">{stats.totalQuantity}</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">Single Copies</p>
              <p className="text-2xl font-bold">{stats.singleCopies}</p>
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">With Duplicates</p>
              <p className="text-2xl font-bold">{stats.withDuplicates}</p>
              {stats.duplicates > 0 && (
                <p className="text-xs text-muted-foreground">
                  ({stats.duplicates} extra copies)
                </p>
              )}
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <AlertCircle className="h-6 w-6 mx-auto mb-2 text-blue-600" />
            <p className="text-center text-blue-700">
              Advanced statistics (rarity breakdown, type distribution, set completion rankings) coming in future updates
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CollectionStats;
