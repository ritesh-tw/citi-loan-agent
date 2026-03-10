"use client";

import { useState } from "react";

interface UserInfoFormProps {
  onSubmit: (message: string) => void;
  disabled: boolean;
}

const FIELDS = [
  { key: "full_name", label: "Full Name", placeholder: "John Smith", type: "text" },
  { key: "age", label: "Age", placeholder: "35", type: "number" },
  { key: "email", label: "Email", placeholder: "john@example.com", type: "email" },
  { key: "phone_number", label: "Phone Number", placeholder: "+1 555-0123", type: "tel" },
];

export default function UserInfoForm({ onSubmit, disabled }: UserInfoFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState(false);

  const handleSubmitAll = () => {
    const parts = Object.entries(values)
      .filter(([, v]) => v.trim())
      .map(([k, v]) => {
        const field = FIELDS.find((f) => f.key === k);
        return `${field?.label}: ${v}`;
      });

    if (parts.length > 0) {
      onSubmit(`Here is my information: ${parts.join(", ")}`);
      setValues({});
      setExpanded(false);
    }
  };

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        disabled={disabled}
        className="text-xs text-citi-light hover:text-citi-blue underline mb-2 disabled:opacity-50"
      >
        Fill out form instead
      </button>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
      <h3 className="text-sm font-semibold text-citi-blue mb-3">
        Quick Info Form
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {FIELDS.map((field) => (
          <div key={field.key}>
            <label className="text-xs text-gray-600 font-medium block mb-1">
              {field.label}
            </label>
            <input
              type={field.type}
              placeholder={field.placeholder}
              value={values[field.key] || ""}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, [field.key]: e.target.value }))
              }
              disabled={disabled}
              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-citi-light disabled:opacity-50"
            />
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleSubmitAll}
          disabled={disabled || Object.values(values).every((v) => !v.trim())}
          className="px-4 py-1.5 text-sm bg-citi-blue text-white rounded-lg hover:bg-citi-light transition-colors disabled:opacity-50"
        >
          Submit
        </button>
        <button
          onClick={() => setExpanded(false)}
          className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
