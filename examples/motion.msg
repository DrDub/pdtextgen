NAME msg-motion

SLOTS theme goal msg-time

CONSTANTS go1 to

EQUATIONS
	ltheme = lexicon(theme)
	lgoal = lexicon(goal)

	lgo1 = lexicon(go1 ; ltheme' msg-time)

OUTPUT
	ltheme lgo1 to lgoal

