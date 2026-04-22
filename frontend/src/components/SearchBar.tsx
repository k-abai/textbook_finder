interface SearchBarProps {
  query: string;
  onQueryChange: (value: string) => void;
}

export default function SearchBar({ query, onQueryChange }: SearchBarProps) {
  return (
    <label className="search-bar" htmlFor="book-query">
      <span>Search by title, author, or ISBN</span>
      <input
        id="book-query"
        type="text"
        placeholder="e.g. Calculus, Stewart, 9781285741550"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
      />
    </label>
  );
}
