import { useState } from 'react';
import type { CreateDestinatarioRequest, UpdateDestinatarioRequest } from '@/types';

type FormData = CreateDestinatarioRequest | UpdateDestinatarioRequest;

interface DestinatarioFormProps {
  onSubmit: (data: FormData) => void;
  onCancel: () => void;
  initialData?: Partial<CreateDestinatarioRequest & { cnpj?: string; cpf?: string }>;
  isEdit?: boolean;
  error?: string | null;
}

export function DestinatarioForm({ onSubmit, onCancel, initialData, isEdit = false, error }: DestinatarioFormProps) {
  const initialMode = initialData?.cpf ? 'PF' : 'PJ';
  const [tipo, setTipo] = useState<'PJ' | 'PF'>(initialMode);
  const [cnpj, setCnpj] = useState(initialData?.cnpj ?? '');
  const [cpf, setCpf] = useState(initialData?.cpf ?? '');
  const [razaoSocial, setRazaoSocial] = useState(initialData?.razao_social ?? '');
  const [nomeFantasia, setNomeFantasia] = useState(initialData?.nome_fantasia ?? '');
  const [ie, setIe] = useState(initialData?.ie ?? '');
  const [uf, setUf] = useState(initialData?.uf ?? '');
  const [cidade, setCidade] = useState(initialData?.cidade ?? '');
  const [logradouro, setLogradouro] = useState(initialData?.logradouro ?? '');
  const [numero, setNumero] = useState(initialData?.numero ?? '');
  const [bairro, setBairro] = useState(initialData?.bairro ?? '');
  const [cep, setCep] = useState(initialData?.cep ?? '');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isEdit) {
      const data: UpdateDestinatarioRequest = {
        razao_social: razaoSocial,
        nome_fantasia: nomeFantasia,
        ie,
        uf,
        cidade,
        logradouro,
        numero,
        bairro,
        cep,
      };
      onSubmit(data);
    } else {
      const data: CreateDestinatarioRequest = {
        ...(tipo === 'PJ' ? { cnpj } : { cpf }),
        razao_social: razaoSocial,
        ...(tipo === 'PJ' ? { nome_fantasia: nomeFantasia, ie } : {}),
        uf,
        cidade,
        logradouro,
        numero,
        bairro,
        cep,
      };
      onSubmit(data);
    }
  }

  const inputClass = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm';

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="flex items-center space-x-4">
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="tipo"
            value="PJ"
            checked={tipo === 'PJ'}
            onChange={() => setTipo('PJ')}
            disabled={isEdit}
            aria-label="PJ"
          />
          <span className="ml-1 text-sm">PJ</span>
        </label>
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="tipo"
            value="PF"
            checked={tipo === 'PF'}
            onChange={() => setTipo('PF')}
            disabled={isEdit}
            aria-label="PF"
          />
          <span className="ml-1 text-sm">PF</span>
        </label>
      </div>

      {!isEdit && tipo === 'PJ' && (
        <div>
          <label htmlFor="cnpj" className="block text-sm font-medium text-gray-700">CNPJ</label>
          <input id="cnpj" type="text" value={cnpj} onChange={(e) => setCnpj(e.target.value)} required className={inputClass} />
        </div>
      )}

      {!isEdit && tipo === 'PF' && (
        <div>
          <label htmlFor="cpf" className="block text-sm font-medium text-gray-700">CPF</label>
          <input id="cpf" type="text" value={cpf} onChange={(e) => setCpf(e.target.value)} required className={inputClass} />
        </div>
      )}

      <div>
        <label htmlFor="razao_social" className="block text-sm font-medium text-gray-700">Razao Social</label>
        <input id="razao_social" type="text" value={razaoSocial} onChange={(e) => setRazaoSocial(e.target.value)} required className={inputClass} />
      </div>

      {tipo === 'PJ' && (
        <>
          <div>
            <label htmlFor="nome_fantasia" className="block text-sm font-medium text-gray-700">Nome Fantasia</label>
            <input id="nome_fantasia" type="text" value={nomeFantasia} onChange={(e) => setNomeFantasia(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label htmlFor="ie" className="block text-sm font-medium text-gray-700">IE</label>
            <input id="ie" type="text" value={ie} onChange={(e) => setIe(e.target.value)} className={inputClass} />
          </div>
        </>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="uf" className="block text-sm font-medium text-gray-700">UF</label>
          <input id="uf" type="text" value={uf} onChange={(e) => setUf(e.target.value)} required maxLength={2} className={inputClass} />
        </div>
        <div>
          <label htmlFor="cidade" className="block text-sm font-medium text-gray-700">Cidade</label>
          <input id="cidade" type="text" value={cidade} onChange={(e) => setCidade(e.target.value)} required className={inputClass} />
        </div>
      </div>

      <div>
        <label htmlFor="logradouro" className="block text-sm font-medium text-gray-700">Logradouro</label>
        <input id="logradouro" type="text" value={logradouro} onChange={(e) => setLogradouro(e.target.value)} required className={inputClass} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="numero" className="block text-sm font-medium text-gray-700">Numero</label>
          <input id="numero" type="text" value={numero} onChange={(e) => setNumero(e.target.value)} required className={inputClass} />
        </div>
        <div>
          <label htmlFor="bairro" className="block text-sm font-medium text-gray-700">Bairro</label>
          <input id="bairro" type="text" value={bairro} onChange={(e) => setBairro(e.target.value)} required className={inputClass} />
        </div>
      </div>

      <div>
        <label htmlFor="cep" className="block text-sm font-medium text-gray-700">CEP</label>
        <input id="cep" type="text" value={cep} onChange={(e) => setCep(e.target.value)} required className={inputClass} />
      </div>

      <div className="flex justify-end space-x-3">
        <button type="button" onClick={onCancel}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Cancelar
        </button>
        <button type="submit"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
          Salvar
        </button>
      </div>
    </form>
  );
}
