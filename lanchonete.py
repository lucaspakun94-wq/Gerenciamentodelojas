import customtkinter as ctk
import json
import datetime
import os
from tkinter import messagebox
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Configurações de aparência
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SistemaLanchonete(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Define a pasta de dados (ficheiros)
        self.pasta_dados = "dados_lanchonete"
        if not os.path.exists(self.pasta_dados):
            os.makedirs(self.pasta_dados)
            
        self.ARQUIVO_PRODUTOS = os.path.join(self.pasta_dados, "produtos.json")
        self.ARQUIVO_ESTOQUE = os.path.join(self.pasta_dados, "estoque.json")
        self.ARQUIVO_VENDAS = os.path.join(self.pasta_dados, "vendas.json")

        self.produtos = self.carregar_dados(self.ARQUIVO_PRODUTOS, {})
        self.estoque = self.carregar_dados(self.ARQUIVO_ESTOQUE, {})
        self.vendas = self.carregar_dados(self.ARQUIVO_VENDAS, [])

        self.title("Sistema Lanchonete - Gestão")
        self.geometry("1000x700") # Aumentei um pouco para acomodar o carrinho gracioso

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        fonte_botoes = ctk.CTkFont(family="Arial", size=15, weight="bold")

        # --- MENU LATERAL ---
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="LANCHONETE", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.pack(pady=30)

        # Botões do Menu atualizados
        self.btn_venda = ctk.CTkButton(self.sidebar_frame, text="Nova Venda", height=45, font=fonte_botoes, command=self.mostrar_venda)
        self.btn_venda.pack(pady=10, padx=20, fill="x")

        self.btn_estoque = ctk.CTkButton(self.sidebar_frame, text="Ver Estoque", height=45, font=fonte_botoes, command=self.mostrar_estoque)
        self.btn_estoque.pack(pady=10, padx=20, fill="x")
        
        self.btn_reposicao = ctk.CTkButton(self.sidebar_frame, text="Repor Estoque", height=45, font=fonte_botoes, command=self.mostrar_reposicao)
        self.btn_reposicao.pack(pady=10, padx=20, fill="x")

        self.btn_cadastrar = ctk.CTkButton(self.sidebar_frame, text="Cadastrar Item", height=45, font=fonte_botoes, command=self.mostrar_cadastro)
        self.btn_cadastrar.pack(pady=10, padx=20, fill="x")
        
        self.btn_gerir = ctk.CTkButton(self.sidebar_frame, text="Gerir Produtos", height=45, font=fonte_botoes, command=self.mostrar_gestao)
        self.btn_gerir.pack(pady=10, padx=20, fill="x")

        self.btn_pdf = ctk.CTkButton(self.sidebar_frame, text="Gerar Relatório PDF", height=45, font=fonte_botoes, fg_color="green", command=self.gerar_pdf_vendas)
        self.btn_pdf.pack(side="bottom", pady=30, padx=20, fill="x")

        # --- CONTEÚDO PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.mostrar_estoque()

    # --- FUNÇÕES DE DADOS ---
    def carregar_dados(self, arquivo, valor_padrao):
        if not os.path.exists(arquivo):
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(valor_padrao, f)
            return valor_padrao
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return valor_padrao

    def salvar_dados(self, dados, arquivo):
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except PermissionError:
            messagebox.showerror("Aviso", f"O ficheiro {arquivo} está aberto noutro programa. Por favor, fecha-o e tente de novo.")
        except Exception as e:
            messagebox.showerror("Contratempo", f"Tivemos um pequeno contratempo: {e}")

    def limpar_ecra(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- 1. CARRINHO DE COMPRAS (NOVA VENDA MÚLTIPLA) ---
    def mostrar_venda(self):
        self.limpar_ecra()
        self.carrinho_atual = [] # Lista temporária para os itens da venda
        
        ctk.CTkLabel(self.main_frame, text="Registo de Venda (Carrinho)", font=("Arial", 26, "bold")).pack(pady=20)
        
        fonte_labels = ctk.CTkFont(size=14)
        
        # Área de inserção superior
        frame_inputs = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_inputs.pack(fill="x", padx=40)
        
        ctk.CTkLabel(frame_inputs, text="Código do Produto:", font=fonte_labels).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        entry_cod = ctk.CTkEntry(frame_inputs, width=150, height=40, font=fonte_labels)
        entry_cod.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(frame_inputs, text="Quantidade:", font=fonte_labels).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        entry_qtd = ctk.CTkEntry(frame_inputs, width=100, height=40, font=fonte_labels)
        entry_qtd.grid(row=0, column=3, padx=10, pady=10)
        entry_qtd.insert(0, "1") # Quantidade padrão

        caixa_carrinho = ctk.CTkTextbox(self.main_frame, width=700, height=250, font=("Courier New", 14))
        caixa_carrinho.pack(pady=20)
        caixa_carrinho.configure(state="disabled")
        
        label_total = ctk.CTkLabel(self.main_frame, text="Total: 0.00 R$", font=("Arial", 20, "bold"), text_color="green")
        label_total.pack(pady=5)

        def atualizar_ecra_carrinho():
            caixa_carrinho.configure(state="normal")
            caixa_carrinho.delete("0.0", "end")
            texto = "--- ITENS NO CARRINHO ---\n\n"
            total = 0.0
            for item in self.carrinho_atual:
                subtotal = item['preco'] * item['qtd']
                total += subtotal
                texto += f"{item['nome'][:20]:<22} | Qtd: {item['qtd']:<3} | Subtotal: {subtotal:.2f} R$\n"
            caixa_carrinho.insert("0.0", texto)
            caixa_carrinho.configure(state="disabled")
            label_total.configure(text=f"Total: {total:.2f} R$")
            return total

        def adicionar_ao_carrinho():
            cod = entry_cod.get()
            try:
                qtd_pedida = int(entry_qtd.get())
                if qtd_pedida <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Por favor, insere uma quantidade válida.")
                return

            if cod in self.produtos:
                # Verificar se já existe no carrinho para somar a quantidade e validar o stock
                qtd_ja_no_carrinho = sum(item['qtd'] for item in self.carrinho_atual if item['cod'] == cod)
                if self.estoque.get(cod, 0) >= (qtd_ja_no_carrinho + qtd_pedida):
                    self.carrinho_atual.append({
                        "cod": cod,
                        "nome": self.produtos[cod]['nome'],
                        "preco": self.produtos[cod]['preco'],
                        "qtd": qtd_pedida
                    })
                    atualizar_ecra_carrinho()
                    entry_cod.delete(0, 'end')
                    entry_qtd.delete(0, 'end')
                    entry_qtd.insert(0, "1")
                else:
                    messagebox.showwarning("Estoque Insuficiente", "Não temos essa quantidade toda disponível no momento!")
            else:
                messagebox.showwarning("Não Encontrado", "Código de produto não reconhecido.")

        def finalizar_compra():
            if not self.carrinho_atual:
                messagebox.showinfo("Aviso", "O carrinho está vazio")
                return
            
            total_venda = atualizar_ecra_carrinho()
            detalhes_itens = []
            
            # Abater do stock e preparar registo
            for item in self.carrinho_atual:
                self.estoque[item['cod']] -= item['qtd']
                detalhes_itens.append(f"{item['qtd']}x {item['nome']}")
                
            nova_venda = {
                "data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                "item": ", ".join(detalhes_itens), # Junta todos os nomes
                "qtd": sum(item['qtd'] for item in self.carrinho_atual),
                "total": total_venda
            }
            
            self.vendas.append(nova_venda)
            self.salvar_dados(self.estoque, self.ARQUIVO_ESTOQUE)
            self.salvar_dados(self.vendas, self.ARQUIVO_VENDAS)
            
            messagebox.showinfo("Sucesso", f"Que maravilha! Venda de {total_venda:.2f} R$ finalizada com sucesso!")
            self.mostrar_venda() # Limpa o ecrã para a próxima

        ctk.CTkButton(frame_inputs, text="Adicionar Item", height=40, font=("Arial", 14, "bold"), command=adicionar_ao_carrinho).grid(row=0, column=4, padx=20)
        ctk.CTkButton(self.main_frame, text="Finalizar Compra", height=55, width=300, font=("Arial", 18, "bold"), fg_color="green", command=finalizar_compra).pack(pady=20)

    # --- 2. REPOSIÇÃO DE ESTOQUE ---
    def mostrar_reposicao(self):
        self.limpar_ecra()
        ctk.CTkLabel(self.main_frame, text="Reposição Rápida de estoque", font=("Arial", 26, "bold")).pack(pady=30)
        
        fonte_labels = ctk.CTkFont(size=14)

        ctk.CTkLabel(self.main_frame, text="Código do Produto:", font=fonte_labels).pack(pady=(10, 0))
        entry_cod = ctk.CTkEntry(self.main_frame, width=350, height=40, font=fonte_labels)
        entry_cod.pack(pady=5)
        
        ctk.CTkLabel(self.main_frame, text="Quantidade Recebida:", font=fonte_labels).pack(pady=(10, 0))
        entry_qtd = ctk.CTkEntry(self.main_frame, width=350, height=40, font=fonte_labels)
        entry_qtd.pack(pady=5)

        def confirmar_reposicao():
            cod = entry_cod.get()
            if cod in self.estoque:
                try:
                    qtd = int(entry_qtd.get())
                    self.estoque[cod] += qtd
                    self.salvar_dados(self.estoque, self.ARQUIVO_ESTOQUE)
                    messagebox.showinfo("Sucesso", f"O stock do item '{self.produtos[cod]['nome']}' foi atualizado com carinho!")
                    self.mostrar_estoque()
                except ValueError:
                    messagebox.showerror("Atenção", "Por favor, insere um número válido.")
            else:
                messagebox.showerror("Não Encontrado", "Esse código não está registado no nosso catálogo.")

        ctk.CTkButton(self.main_frame, text="Adicionar ao Estoque", height=55, width=300, font=("Arial", 18, "bold"), command=confirmar_reposicao).pack(pady=40)

    # --- 3. EDIÇÃO E EXCLUSÃO DE PRODUTOS ---
    def mostrar_gestao(self):
        self.limpar_ecra()
        ctk.CTkLabel(self.main_frame, text="Gestão do Catálogo (Editar/Remover)", font=("Arial", 26, "bold")).pack(pady=20)
        
        fonte_labels = ctk.CTkFont(size=14)

        frame_busca = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_busca.pack(pady=10)
        
        ctk.CTkLabel(frame_busca, text="Código:", font=fonte_labels).grid(row=0, column=0, padx=5)
        entry_busca = ctk.CTkEntry(frame_busca, width=150, height=40)
        entry_busca.grid(row=0, column=1, padx=5)
        
        frame_edicao = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        ctk.CTkLabel(frame_edicao, text="Novo Nome:", font=fonte_labels).pack(pady=(10,0))
        entry_nome = ctk.CTkEntry(frame_edicao, width=350, height=40, font=fonte_labels)
        entry_nome.pack()
        
        ctk.CTkLabel(frame_edicao, text="Novo Preço (R$):", font=fonte_labels).pack(pady=(10,0))
        entry_preco = ctk.CTkEntry(frame_edicao, width=350, height=40, font=fonte_labels)
        entry_preco.pack()

        def buscar_produto():
            cod = entry_busca.get()
            if cod in self.produtos:
                entry_nome.delete(0, 'end')
                entry_nome.insert(0, self.produtos[cod]['nome'])
                entry_preco.delete(0, 'end')
                entry_preco.insert(0, str(self.produtos[cod]['preco']))
                frame_edicao.pack(pady=20) # Mostra os campos de edição
                frame_botoes.pack(pady=10)
            else:
                messagebox.showinfo("Aviso", "Item não encontrado no catálogo.")
                frame_edicao.pack_forget()
                frame_botoes.pack_forget()

        ctk.CTkButton(frame_busca, text="Buscar", height=40, command=buscar_produto).grid(row=0, column=2, padx=10)

        frame_botoes = ctk.CTkFrame(self.main_frame, fg_color="transparent")

        def atualizar_produto():
            cod = entry_busca.get()
            try:
                novo_n = entry_nome.get()
                novo_p = float(entry_preco.get().replace(',', '.'))
                self.produtos[cod] = {"nome": novo_n, "preco": novo_p}
                self.salvar_dados(self.produtos, self.ARQUIVO_PRODUTOS)
                messagebox.showinfo("Sucesso", "Os detalhes foram atualizados!")
                self.mostrar_estoque()
            except ValueError:
                messagebox.showerror("Atenção", "O valor do preço não é válido.")

        def eliminar_produto():
            cod = entry_busca.get()
            resposta = messagebox.askyesno("Confirmar", f"Desejas mesmo retirar o item '{self.produtos[cod]['nome']}' do catálogo?")
            if resposta:
                del self.produtos[cod]
                if cod in self.estoque:
                    del self.estoque[cod]
                self.salvar_dados(self.produtos, self.ARQUIVO_PRODUTOS)
                self.salvar_dados(self.estoque, self.ARQUIVO_ESTOQUE)
                messagebox.showinfo("Feito", "Item removido com sucesso.")
                self.mostrar_estoque()

        ctk.CTkButton(frame_botoes, text="Guardar Alterações", height=45, fg_color="blue", command=atualizar_produto).grid(row=0, column=0, padx=10)
        ctk.CTkButton(frame_botoes, text="Retirar do Catálogo", height=45, fg_color="#D9534F", hover_color="#C9302C", command=eliminar_produto).grid(row=0, column=1, padx=10)

    # --- TELAS ORIGINAIS (ESTOQUE, CADASTRO, PDF) MANTIDAS INTACTAS ---
    def mostrar_estoque(self):
        self.limpar_ecra()
        ctk.CTkLabel(self.main_frame, text="Estoque Atual", font=("Arial", 26, "bold")).pack(pady=20)
        tabela = ctk.CTkTextbox(self.main_frame, width=700, height=450, font=("Courier New", 14))
        tabela.pack(pady=10, padx=20)
        texto = f"{'CÓDIGO':<10} | {'PRODUTO':<25} | {'QTD':<5} | {'PREÇO'}\n" + "-"*65 + "\n"
        for cod, qtd in self.estoque.items():
            prod = self.produtos.get(cod, {"nome": "N/A", "preco": 0.0})
            texto += f"{cod:<10} | {prod['nome'][:23]:<25} | {qtd:<5} | {prod['preco']:.2f} R$\n"
        tabela.insert("0.0", texto)
        tabela.configure(state="disabled")

    def mostrar_cadastro(self):
        self.limpar_ecra()
        ctk.CTkLabel(self.main_frame, text="Adicionar ao Catálogo", font=("Arial", 26, "bold")).pack(pady=30)
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        container.pack()
        entries = {}
        campos = [("Código do Produto:", "cod"), ("Nome do Produto:", "nome"), ("Preço (R$):", "preco"), ("Estoque Inicial:", "qtd")]
        fonte_labels = ctk.CTkFont(size=14)
        for label, key in campos:
            ctk.CTkLabel(container, text=label, font=fonte_labels).pack(anchor="w", pady=(10, 0))
            entry = ctk.CTkEntry(container, width=350, height=40, font=fonte_labels)
            entry.pack(pady=5)
            entries[key] = entry
        def salvar():
            try:
                c, n, p, q = entries['cod'].get(), entries['nome'].get(), float(entries['preco'].get().replace(',', '.')), int(entries['qtd'].get())
                if c in self.produtos:
                    messagebox.showwarning("Atenção", "Este código já existe!")
                    return
                self.produtos[c] = {"nome": n, "preco": p}
                self.estoque[c] = q
                self.salvar_dados(self.produtos, self.ARQUIVO_PRODUTOS)
                self.salvar_dados(self.estoque, self.ARQUIVO_ESTOQUE)
                messagebox.showinfo("Sucesso", f"O item '{n}' foi adicionado corretamente!")
                self.mostrar_estoque()
            except ValueError:
                messagebox.showerror("Erro", "Por favor, preenche os valores corretamente!")
        ctk.CTkButton(self.main_frame, text="Confirmar Cadastro", height=55, width=300, font=("Arial", 18, "bold"), command=salvar).pack(pady=40)

    def gerar_pdf_vendas(self):
        nome_arquivo = f"Relatorio_Vendas_{datetime.date.today()}.pdf"
        c = canvas.Canvas(nome_arquivo, pagesize=letter)
        largura, altura = letter
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, altura - 50, "RELATÓRIO DE VENDAS - LANCHONETE")
        c.setFont("Helvetica", 10)
        c.drawString(50, altura - 70, f"Gerado a: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y = altura - 110
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Data")
        c.drawString(180, y, "Produto(s)")
        c.drawString(450, y, "Total (R$)")
        c.line(50, y-5, 550, y-5)
        y -= 25
        total_geral = 0
        c.setFont("Helvetica", 10)
        for v in self.vendas:
            c.drawString(50, y, v['data'])
            c.drawString(180, y, v['item'][:45] + "..." if len(v['item']) > 45 else v['item'])
            c.drawString(450, y, f"{v['total']:.2f} R$")
            total_geral += v['total']
            y -= 20
            if y < 50:
                c.showPage()
                y = altura - 50
        c.line(50, y, 550, y)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, y - 25, f"TOTAL ACUMULADO: {total_geral:.2f} R$")
        c.save()
        messagebox.showinfo("PDF Gerado", f"O relatório '{nome_arquivo}' está pronto.")

if __name__ == "__main__":
    app = SistemaLanchonete()
    app.mainloop()