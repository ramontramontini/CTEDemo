interface ValidationErrorsProps {
  errors: Record<string, string> | null;
}

export function ValidationErrors({ errors }: ValidationErrorsProps) {
  if (!errors || Object.keys(errors).length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-sm font-medium text-red-800 mb-2">Erros de validação</h3>
      <ul className="space-y-1">
        {Object.entries(errors).map(([field, message]) => (
          <li key={field} className="text-sm text-red-700 flex items-start gap-2">
            <span className="text-red-400 mt-0.5">&#x2715;</span>
            <span>{message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
