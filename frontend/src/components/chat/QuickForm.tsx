"use client";

import { useState } from "react";

interface QuickFormProps {
  onSubmit: (message: string) => void;
  disabled: boolean;
  formType: "identity" | "personal_info" | "prequalification" | null;
}

const IDENTITY_FIELDS = [
  { key: "last_name", label: "Last Name", placeholder: "Thompson", type: "text" },
  { key: "postcode", label: "Postcode", placeholder: "SW1A 1AA", type: "text" },
  { key: "dob", label: "Date of Birth", placeholder: "15/03/1985", type: "text" },
];

const PERSONAL_INFO_FIELDS = [
  { key: "full_name", label: "Full Name", placeholder: "John Smith", type: "text" },
  { key: "dob", label: "Date of Birth", placeholder: "15/03/1985", type: "text" },
  { key: "postcode", label: "Postcode", placeholder: "SW1A 1AA", type: "text" },
  { key: "email", label: "Email", placeholder: "john@example.com", type: "email" },
  { key: "phone", label: "Phone", placeholder: "+44 7700 900123", type: "tel" },
];

const PREQUAL_FIELDS = [
  {
    key: "employment_status",
    label: "Employment",
    type: "select",
    options: [
      { value: "", label: "Select..." },
      { value: "full_time", label: "Full-time" },
      { value: "part_time", label: "Part-time" },
      { value: "self_employed", label: "Self-employed" },
      { value: "retired", label: "Retired" },
      { value: "unemployed", label: "Unemployed" },
    ],
  },
  { key: "annual_income", label: "Annual Income (£)", placeholder: "45000", type: "number" },
  { key: "loan_amount", label: "Loan Amount (£)", placeholder: "15000", type: "number" },
  {
    key: "loan_purpose",
    label: "Purpose",
    type: "select",
    options: [
      { value: "", label: "Select..." },
      { value: "personal", label: "Personal" },
      { value: "debt_consolidation", label: "Debt Consolidation" },
      { value: "home_improvement", label: "Home Improvement" },
      { value: "car", label: "Car" },
      { value: "holiday", label: "Holiday" },
      { value: "wedding", label: "Wedding" },
      { value: "other", label: "Other" },
    ],
  },
  {
    key: "repayment_term",
    label: "Term (months)",
    type: "select",
    options: [
      { value: "", label: "Select..." },
      { value: "12", label: "12 months" },
      { value: "24", label: "24 months" },
      { value: "36", label: "36 months" },
      { value: "48", label: "48 months" },
      { value: "60", label: "60 months" },
      { value: "84", label: "84 months" },
    ],
  },
  {
    key: "residency_status",
    label: "Residency",
    type: "select",
    options: [
      { value: "", label: "Select..." },
      { value: "uk_resident", label: "UK Resident" },
      { value: "uk_visa", label: "UK Visa Holder" },
      { value: "non_resident", label: "Non-Resident" },
    ],
  },
];

const FORM_CONFIG = {
  identity: {
    fields: IDENTITY_FIELDS,
    title: "Identity Verification",
    buttonLabel: "Open Identity Form",
    hint: "You can type your details or use the quick form:",
    cols: "grid-cols-3",
  },
  personal_info: {
    fields: PERSONAL_INFO_FIELDS,
    title: "Personal Details",
    buttonLabel: "Open Personal Info Form",
    hint: "You can type your details or fill the form:",
    cols: "grid-cols-3",
  },
  prequalification: {
    fields: PREQUAL_FIELDS,
    title: "Loan Application Details",
    buttonLabel: "Open Application Form",
    hint: "You can reply in chat or fill all fields at once:",
    cols: "grid-cols-3",
  },
};

export default function QuickForm({ onSubmit, disabled, formType }: QuickFormProps) {
  const [expanded, setExpanded] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});

  if (!formType) return null;

  const config = FORM_CONFIG[formType];
  const fields = config.fields;

  const handleSubmit = () => {
    const filledFields = Object.entries(values).filter(([, v]) => v.trim());
    if (filledFields.length === 0) return;

    let message = "";
    if (formType === "identity") {
      const parts: string[] = [];
      if (values.last_name) parts.push(`My last name is ${values.last_name}`);
      if (values.postcode) parts.push(`postcode is ${values.postcode}`);
      if (values.dob) parts.push(`date of birth is ${values.dob}`);
      message = parts.join(", ") + ".";
    } else if (formType === "personal_info") {
      const parts: string[] = [];
      if (values.full_name) parts.push(`My name is ${values.full_name}`);
      if (values.dob) parts.push(`date of birth is ${values.dob}`);
      if (values.postcode) parts.push(`postcode is ${values.postcode}`);
      if (values.email) parts.push(`email is ${values.email}`);
      if (values.phone) parts.push(`phone is ${values.phone}`);
      message = parts.join(", ") + ".";
    } else {
      const parts: string[] = [];
      if (values.employment_status) parts.push(`I work ${values.employment_status.replace("_", " ")}`);
      if (values.annual_income) parts.push(`earn £${values.annual_income} per year`);
      if (values.loan_amount) parts.push(`want to borrow £${values.loan_amount}`);
      if (values.loan_purpose) parts.push(`for ${values.loan_purpose.replace("_", " ")}`);
      if (values.repayment_term) parts.push(`over ${values.repayment_term} months`);
      if (values.residency_status) parts.push(`I am a ${values.residency_status.replace("_", " ")}`);
      message = parts.join(", ") + ".";
    }

    onSubmit(message);
    setValues({});
    setExpanded(false);
  };

  if (!expanded) {
    return (
      <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
        <span className="text-xs text-gray-500">{config.hint}</span>
        <button
          onClick={() => setExpanded(true)}
          disabled={disabled}
          className="text-xs font-medium bg-citi-blue text-white px-3 py-1 rounded-full hover:bg-citi-light transition-colors disabled:opacity-50 whitespace-nowrap"
        >
          {config.buttonLabel}
        </button>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-2">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-semibold text-citi-blue">{config.title}</h4>
        <button
          onClick={() => setExpanded(false)}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          Close
        </button>
      </div>
      <p className="text-[10px] text-gray-400 mb-2">
        Fill in the fields below and submit, or close this and type your answers in the chat.
      </p>
      <div className={`grid ${config.cols} gap-2`}>
        {fields.map((field) => (
          <div key={field.key}>
            <label className="text-[10px] text-gray-500 font-medium block mb-0.5">
              {field.label}
            </label>
            {field.type === "select" && "options" in field ? (
              <select
                value={values[field.key] || ""}
                onChange={(e) => setValues((prev) => ({ ...prev, [field.key]: e.target.value }))}
                disabled={disabled}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-citi-light bg-white disabled:opacity-50"
              >
                {("options" in field ? field.options : [])?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type}
                placeholder={"placeholder" in field ? field.placeholder : ""}
                value={values[field.key] || ""}
                onChange={(e) => setValues((prev) => ({ ...prev, [field.key]: e.target.value }))}
                disabled={disabled}
                className="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-citi-light disabled:opacity-50"
              />
            )}
          </div>
        ))}
      </div>
      <button
        onClick={handleSubmit}
        disabled={disabled || Object.values(values).every((v) => !v.trim())}
        className="mt-2 px-4 py-1 text-xs bg-citi-blue text-white rounded-lg hover:bg-citi-light transition-colors disabled:opacity-50"
      >
        Submit All
      </button>
    </div>
  );
}
