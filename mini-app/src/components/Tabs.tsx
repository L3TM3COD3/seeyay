import { Category } from '../api/client';

interface TabsProps {
  categories: Category[];
  activeCategory: string;
  onCategoryChange: (category: string) => void;
}

export function Tabs({ categories, activeCategory, onCategoryChange }: TabsProps) {
  return (
    <div className="tabs">
      {categories.map((category) => (
        <button
          key={category.id}
          className={`tab ${activeCategory === category.id ? 'active' : ''}`}
          onClick={() => onCategoryChange(category.id)}
        >
          {category.name}
        </button>
      ))}
    </div>
  );
}
