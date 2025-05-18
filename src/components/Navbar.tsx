import { useState, useEffect } from 'react';
import { useCollection } from '@/lib/collection';
import { 
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MoonIcon, SunIcon } from '@radix-ui/react-icons';
import { Codesandbox, CreditCard, LayoutGrid, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavbarProps {
  view: 'sets' | 'cards' | 'collection';
  onSetSelectView: (view: 'sets' | 'cards' | 'collection') => void;
}

const Navbar: React.FC<NavbarProps> = ({ view, onSetSelectView }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const { getCollectionCards } = useCollection();
  
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', newTheme);
  };
  
  useEffect(() => {
    // Check for user preference in localStorage
    const savedTheme = localStorage.getItem('theme');
    
    // Check for system preference
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
      setTheme('dark');
      document.documentElement.classList.add('dark');
    } else {
      setTheme('light');
      document.documentElement.classList.remove('dark');
    }
  }, []);
  
  const collectionSize = getCollectionCards().length;
  
  return (
    <div className="border-b sticky top-0 z-40 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem className="mr-2">
                <Button
                  asChild
                  variant="link"
                  className={cn(
                    navigationMenuTriggerStyle(),
                    view === 'sets' && "text-primary font-semibold"
                  )}
                  onClick={() => onSetSelectView('sets')}
                >
                  <div className="flex items-center">
                    <LayoutGrid className="mr-2 h-4 w-4" />
                    Sets
                  </div>
                </Button>
              </NavigationMenuItem>
              
              <NavigationMenuItem>
                <Button
                  asChild
                  variant="link"
                  className={cn(
                    navigationMenuTriggerStyle(),
                    view === 'collection' && "text-primary font-semibold"
                  )}
                  onClick={() => onSetSelectView('collection')}
                >
                  <div className="flex items-center">
                    <CreditCard className="mr-2 h-4 w-4" />
                    My Collection
                    {collectionSize > 0 && (
                      <Badge className="ml-2 bg-primary">{collectionSize}</Badge>
                    )}
                  </div>
                </Button>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>
        
        <div className="flex items-center justify-between flex-1 md:justify-end">
          <div className="flex items-center md:hidden">
            <Button variant="ghost" size="icon" className="mr-2" asChild
              onClick={() => onSetSelectView('sets')}
            >
              <div className={cn(
                "p-2 rounded-md",
                view === 'sets' && "bg-muted"
              )}>
                <LayoutGrid className="h-5 w-5" />
              </div>
            </Button>
            
            <Button variant="ghost" size="icon" className="relative" asChild
              onClick={() => onSetSelectView('collection')}
            >
              <div className={cn(
                "p-2 rounded-md",
                view === 'collection' && "bg-muted"
              )}>
                <CreditCard className="h-5 w-5" />
                {collectionSize > 0 && (
                  <Badge className="absolute -top-1 -right-1 text-xs w-5 h-5 flex items-center justify-center p-0 rounded-full">
                    {collectionSize}
                  </Badge>
                )}
              </div>
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? (
                <MoonIcon className="h-5 w-5" />
              ) : (
                <SunIcon className="h-5 w-5" />
              )}
            </Button>
            
            <a 
              href="https://pokemontcg.io" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors ml-2 hidden sm:block"
            >
              Powered by Pokémon TCG API
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navbar;