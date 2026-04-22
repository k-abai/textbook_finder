import type { Textbook } from '../lib/types';

interface TextbookCardProps {
  textbook: Textbook;
}

const availabilityLabel: Record<Textbook['availability'], string> = {
  in_stock: 'In Stock',
  limited: 'Limited',
  out_of_stock: 'Out of Stock'
};

export default function TextbookCard({ textbook }: TextbookCardProps) {
  return (
    <article className="card">
      <header>
        <h3>{textbook.title}</h3>
        <span className={`badge ${textbook.availability}`}>
          {availabilityLabel[textbook.availability]}
        </span>
      </header>
      <p className="meta">{textbook.author}</p>
      <p className="meta">
        ISBN: {textbook.isbn} · Edition: {textbook.edition}
      </p>
      <p className="meta">
        {textbook.store} · {textbook.condition}
      </p>
      <p className="price">${textbook.price.toFixed(2)}</p>
    </article>
  );
}
