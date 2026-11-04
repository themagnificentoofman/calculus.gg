CREATE TABLE `cbank_family_lineage` (
	`family_id` text PRIMARY KEY NOT NULL,
	`construction_id` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cbank_problem_lineage` (
	`problem_id` text PRIMARY KEY NOT NULL,
	`lineage_id` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cbank_release_exclusions` (
	`release_id` text NOT NULL,
	`problem_ref` integer NOT NULL,
	`scope` text NOT NULL,
	`reason` text NOT NULL,
	PRIMARY KEY(`release_id`, `problem_ref`)
);
--> statement-breakpoint
CREATE TABLE `cbank_withdrawn_families` (
	`source_release_id` text NOT NULL,
	`family_id` text NOT NULL,
	`introduced_by` text NOT NULL,
	`reason` text NOT NULL,
	PRIMARY KEY(`source_release_id`, `family_id`, `introduced_by`)
);

--> statement-breakpoint
CREATE TRIGGER cbank_family_lineage_immutable BEFORE UPDATE ON cbank_family_lineage BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_family_lineage_retained BEFORE DELETE ON cbank_family_lineage BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_problem_lineage_immutable BEFORE UPDATE ON cbank_problem_lineage BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_problem_lineage_retained BEFORE DELETE ON cbank_problem_lineage BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_release_exclusions_immutable BEFORE UPDATE ON cbank_release_exclusions BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_release_exclusions_retained BEFORE DELETE ON cbank_release_exclusions BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_withdrawn_families_immutable BEFORE UPDATE ON cbank_withdrawn_families BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;

--> statement-breakpoint
CREATE TRIGGER cbank_withdrawn_families_retained BEFORE DELETE ON cbank_withdrawn_families BEGIN SELECT RAISE(ABORT,'Retain reviewed release policy; create a new release'); END;
