import type { ValidationError } from '@/types';

interface ValidationErrorsProps {
  errors: ValidationError[] | null;
}

export function ValidationErrors({ errors }: ValidationErrorsProps) {
  if (!errors || errors.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-sm font-medium text-red-800 mb-2">Erros de validação</h3>
      <ul className="space-y-1">
        {errors.map((error, index) => (
          <li key={index} className="text-sm text-red-700 flex items-start gap-2">
            <span className="text-red-400 mt-0.5">&#x2715;</span>
            <span>{error.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
