import { useState } from 'react';
import { PokemonCard, PokemonSet } from './lib/api';
import Navbar from './components/Navbar';
import SetGrid from './components/SetGrid';
import CardGrid from './components/CardGrid';
import CardDetail from './components/CardDetail';
import CollectionView from './components/CollectionView';
import { ThemeProvider } from 'next-themes';
import { Toaster } from '@/components/ui/toaster';

function App() {
  const [view, setView] = useState<'sets' | 'cards' | 'collection'>('sets');
  const [selectedSet, setSelectedSet] = useState<PokemonSet | null>(null);
  const [selectedCard, setSelectedCard] = useState<PokemonCard | null>(null);
  const [showCardDetail, setShowCardDetail] = useState(false);

  const handleSetSelect = (set: PokemonSet) => {
    setSelectedSet(set);
    setView('cards');
  };

  const handleBackToSets = () => {
    setView('sets');
  };

  const handleCardSelect = (card: PokemonCard) => {
    setSelectedCard(card);
    setShowCardDetail(true);
  };

  const handleSetView = (newView: 'sets' | 'cards' | 'collection') => {
    if (newView === 'sets') {
      setSelectedSet(null);
    }
    setView(newView);
  };

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <div className="min-h-screen bg-background">
        <Navbar view={view} onSetSelectView={handleSetView} />
        
        <main>
          {view === 'sets' && (
            <SetGrid onSetSelect={handleSetSelect} />
          )}
          
          {view === 'cards' && selectedSet && (
            <CardGrid 
              selectedSet={selectedSet}
              onBackClick={handleBackToSets}
              onCardSelect={handleCardSelect}
            />
          )}
          
          {view === 'collection' && (
            <CollectionView />
          )}
        </main>
        
        <CardDetail 
          card={selectedCard}
          open={showCardDetail}
          onOpenChange={setShowCardDetail}
        />
        
        <Toaster />
      </div>
    </ThemeProvider>
  );
}

export default App;