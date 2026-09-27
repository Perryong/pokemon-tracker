import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import SetArtwork from '../SetArtwork';
import { PokemonSet } from '@/lib/types';

it('falls back from a broken logo to the symbol, then a labelled emblem', () => {
  render(<SetArtwork set={{ id: 'wp', name: 'W Promotional', images: { logo: 'logo.webp', symbol: 'symbol.webp' } } as PokemonSet} />);
  fireEvent.error(screen.getByRole('img'));
  expect(screen.getByRole('img')).toHaveAttribute('src', 'symbol.webp');
  fireEvent.error(screen.getByRole('img'));
  expect(screen.getByLabelText('W Promotional catalogue emblem')).toBeInTheDocument();
});
