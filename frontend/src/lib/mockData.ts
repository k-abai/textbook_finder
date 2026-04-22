import type { Textbook } from './types';

export const textbooks: Textbook[] = [
  {
    id: 'tb-1',
    title: 'Introduction to Algorithms',
    author: 'Cormen, Leiserson, Rivest, and Stein',
    isbn: '9780262046305',
    edition: '4th',
    price: 89.99,
    store: 'Campus Books',
    condition: 'used',
    availability: 'in_stock'
  },
  {
    id: 'tb-2',
    title: 'Calculus: Early Transcendentals',
    author: 'James Stewart',
    isbn: '9781285741550',
    edition: '8th',
    price: 120.0,
    store: 'BookBarn Online',
    condition: 'rental',
    availability: 'limited'
  },
  {
    id: 'tb-3',
    title: 'Campbell Biology',
    author: 'Urry, Cain, Wasserman, Minorsky, and Orr',
    isbn: '9780135988046',
    edition: '12th',
    price: 132.5,
    store: 'Textbook Hub',
    condition: 'new',
    availability: 'out_of_stock'
  }
];
