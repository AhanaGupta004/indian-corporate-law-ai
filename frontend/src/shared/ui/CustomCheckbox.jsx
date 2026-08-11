import { Check } from 'lucide-react'

export default function CustomCheckbox({ checked, onChange, label, required = false, disabled = false }) {
  return (
    <label className={`flex items-start gap-3 cursor-pointer group ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
      <div className="relative flex items-center justify-center shrink-0 mt-0.5">
        <input
          type="checkbox"
          className="peer sr-only"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          required={required}
          disabled={disabled}
        />
        <div className={`w-5 h-5 rounded border transition-all flex items-center justify-center
          ${checked 
            ? 'bg-orange-500 border-orange-500' 
            : 'bg-white dark:bg-[#1a1a1a] border-gray-300 dark:border-neutral-700 group-hover:border-orange-400'
          }`}
        >
          {checked && <Check size={14} className="text-white" strokeWidth={3} />}
        </div>
      </div>
      <span className="text-sm text-gray-600 dark:text-gray-400 font-poppins select-none">
        {label}
      </span>
    </label>
  )
}
