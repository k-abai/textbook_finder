export type Availability = 'in_stock' | 'limited' | 'out_of_stock';

export interface Textbook {
  id: string;
  title: string;
  author: string;
  isbn: string;
  edition: string;
  price: number;
  store: string;
  condition: 'new' | 'used' | 'rental';
  availability: Availability;
}
