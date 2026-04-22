import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

describe('Textbook Finder app', () => {
  it('shows all books by default and filters by search query', async () => {
    render(<App />);

    expect(screen.getByText(/showing 3 of 3 books/i)).toBeInTheDocument();

    const searchInput = screen.getByLabelText(/search by title, author, or isbn/i);
    await userEvent.type(searchInput, 'stewart');

    expect(screen.getByText(/showing 1 of 3 books/i)).toBeInTheDocument();
    expect(screen.getByText(/calculus: early transcendentals/i)).toBeInTheDocument();
  });

  it('renders an empty state for unknown queries', async () => {
    render(<App />);

    const searchInput = screen.getByLabelText(/search by title, author, or isbn/i);
    await userEvent.type(searchInput, 'quantum mythology');

    expect(screen.getByText(/no textbooks found/i)).toBeInTheDocument();
  });
});
