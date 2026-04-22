import { useMemo, useState } from 'react';
import SearchBar from './components/SearchBar';
import TextbookCard from './components/TextbookCard';
import { textbooks } from './lib/mockData';

function normalize(value: string) {
  return value.trim().toLowerCase();
}

export default function App() {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = normalize(query);

    if (!q) {
      return textbooks;
    }

    return textbooks.filter((book) => {
      const haystack = `${book.title} ${book.author} ${book.isbn}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [query]);

  return (
    <main className="container">
      <h1>Textbook Finder</h1>
      <p className="subtitle">Find and compare textbook options across stores.</p>
      <SearchBar query={query} onQueryChange={setQuery} />

      <section className="results" aria-live="polite">
        <p className="result-count">
          Showing {filtered.length} of {textbooks.length} books
        </p>

        <div className="card-grid">
          {filtered.map((book) => (
            <TextbookCard key={book.id} textbook={book} />
          ))}
        </div>

        {filtered.length === 0 && (
          <p className="empty-state">No textbooks found for “{query}”.</p>
        )}
      </section>
    </main>
  );
}
