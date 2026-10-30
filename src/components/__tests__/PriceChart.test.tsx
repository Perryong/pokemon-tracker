import { afterEach, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import PriceChart from '../PriceChart';
afterEach(cleanup);
it('compares real average windows in SGD and distinguishes holo', () => {
  render(<PriceChart prices={{ avg30: 10, avg7: 0, avg1: 20, 'avg7-holo': 30 }} rate={1.5} />);
  expect(screen.getByRole('img', { name: /Reference average prices/ })).toHaveTextContent('SGD 15.00');
  expect(screen.getByText('SGD 0.00')).toBeInTheDocument();
  expect(screen.getByText('SGD 30.00')).toBeInTheDocument();
  expect(screen.getByRole('img', { name: /Holo average prices/ })).toHaveTextContent('SGD 45.00');
  expect(screen.getByText(/overlapping averages/)).toBeInTheDocument();
});
it('omits missing/nonfinite windows and does not invent a chart for marketPrice', () => {
  const { container } = render(<PriceChart prices={{ marketPrice: 10, avg7: Infinity }} rate={1.5} />);
  expect(container).toBeEmptyDOMElement();
});
