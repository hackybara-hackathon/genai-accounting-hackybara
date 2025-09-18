--
-- PostgreSQL database dump
--

\restrict FbcqbBVoqJZ2oUpIvaiKSfQlMNfc34xvQJ4zY0vsV3vyFfrPJ4kkMkAPQFuMxMh

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2025-09-19 01:20:25

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 4903 (class 0 OID 0)
-- Dependencies: 5
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 223 (class 1259 OID 16478)
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    organization_id uuid NOT NULL,
    type character varying(20),
    code character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16491)
-- Name: categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categories (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    organization_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.categories OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16433)
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    organization_id uuid NOT NULL,
    type character varying(20),
    uploaded_by uuid NOT NULL,
    document_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16539)
-- Name: forecasts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forecasts (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    organization_id uuid NOT NULL,
    model_ver character varying(50),
    perdiction_net numeric(10,2),
    month character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.forecasts OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16448)
-- Name: ocr_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ocr_results (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    invoice_number character varying(50),
    invoice_date timestamp without time zone,
    organization_id uuid NOT NULL,
    document_id uuid NOT NULL,
    uploaded_by uuid NOT NULL,
    results text,
    total_amount numeric(10,2),
    currency character varying(10),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    vendor_id uuid
);


ALTER TABLE public.ocr_results OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16397)
-- Name: organizations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.organizations (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.organizations OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16504)
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    description text,
    amount numeric(10,2),
    currency character varying(10),
    invoice_date timestamp without time zone,
    organization_id uuid NOT NULL,
    ocr_result_id uuid,
    vendor_id uuid,
    account_id uuid,
    category_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16405)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    organization_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16420)
-- Name: vendors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendors (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    organization_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.vendors OWNER TO postgres;

--
-- TOC entry 4894 (class 0 OID 16478)
-- Dependencies: 223
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4895 (class 0 OID 16491)
-- Dependencies: 224
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4892 (class 0 OID 16433)
-- Dependencies: 221
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4897 (class 0 OID 16539)
-- Dependencies: 226
-- Data for Name: forecasts; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4893 (class 0 OID 16448)
-- Dependencies: 222
-- Data for Name: ocr_results; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4889 (class 0 OID 16397)
-- Dependencies: 218
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4896 (class 0 OID 16504)
-- Dependencies: 225
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4890 (class 0 OID 16405)
-- Dependencies: 219
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4891 (class 0 OID 16420)
-- Dependencies: 220
-- Data for Name: vendors; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- TOC entry 4722 (class 2606 OID 16485)
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 4724 (class 2606 OID 16498)
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- TOC entry 4718 (class 2606 OID 16442)
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- TOC entry 4728 (class 2606 OID 16545)
-- Name: forecasts forecasts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecasts
    ADD CONSTRAINT forecasts_pkey PRIMARY KEY (id);


--
-- TOC entry 4720 (class 2606 OID 16457)
-- Name: ocr_results ocr_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_results
    ADD CONSTRAINT ocr_results_pkey PRIMARY KEY (id);


--
-- TOC entry 4710 (class 2606 OID 16404)
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- TOC entry 4726 (class 2606 OID 16513)
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 4712 (class 2606 OID 16414)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4714 (class 2606 OID 16412)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4716 (class 2606 OID 16427)
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (id);


--
-- TOC entry 4736 (class 2606 OID 16486)
-- Name: accounts accounts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4737 (class 2606 OID 16499)
-- Name: categories categories_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4731 (class 2606 OID 16443)
-- Name: documents documents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4743 (class 2606 OID 16546)
-- Name: forecasts forecasts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecasts
    ADD CONSTRAINT forecasts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4732 (class 2606 OID 16463)
-- Name: ocr_results ocr_results_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_results
    ADD CONSTRAINT ocr_results_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE RESTRICT;


--
-- TOC entry 4733 (class 2606 OID 16458)
-- Name: ocr_results ocr_results_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_results
    ADD CONSTRAINT ocr_results_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4734 (class 2606 OID 16468)
-- Name: ocr_results ocr_results_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_results
    ADD CONSTRAINT ocr_results_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- TOC entry 4735 (class 2606 OID 16473)
-- Name: ocr_results ocr_results_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocr_results
    ADD CONSTRAINT ocr_results_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendors(id) ON DELETE RESTRICT;


--
-- TOC entry 4738 (class 2606 OID 16529)
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE RESTRICT;


--
-- TOC entry 4739 (class 2606 OID 16534)
-- Name: transactions transactions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE RESTRICT;


--
-- TOC entry 4740 (class 2606 OID 16519)
-- Name: transactions transactions_ocr_result_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_ocr_result_id_fkey FOREIGN KEY (ocr_result_id) REFERENCES public.ocr_results(id) ON DELETE RESTRICT;


--
-- TOC entry 4741 (class 2606 OID 16514)
-- Name: transactions transactions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4742 (class 2606 OID 16524)
-- Name: transactions transactions_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendors(id) ON DELETE RESTRICT;


--
-- TOC entry 4729 (class 2606 OID 16415)
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- TOC entry 4730 (class 2606 OID 16428)
-- Name: vendors vendors_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


-- Completed on 2025-09-19 01:20:25

--
-- PostgreSQL database dump complete
--

\unrestrict FbcqbBVoqJZ2oUpIvaiKSfQlMNfc34xvQJ4zY0vsV3vyFfrPJ4kkMkAPQFuMxMh

